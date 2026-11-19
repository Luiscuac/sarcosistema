import asyncio
import json
from urllib.parse import urlsplit
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.consultas.application.ports.extractor_clinico import ErrorExtractor
from app.consultas.domain.extraccion import validar_propuesta
from app.consultas.infrastructure.ia.prompt import PROMPT_EXTRACCION
from app.consultas.infrastructure.ia.schemas import CapturaModelo

TRespuesta = TypeVar('TRespuesta', bound=BaseModel)


class OllamaExtractor:
    def __init__(self, url='http://127.0.0.1:11434', modelo='qwen2.5:3b', timeout=180, transport=None):
        partes = urlsplit(url)
        if (partes.scheme != 'http' or partes.hostname not in ('127.0.0.1', '::1', 'localhost')
                or partes.username or partes.password or partes.path not in ('', '/')
                or partes.query or partes.fragment):
            raise ValueError('El extractor solo permite Ollama HTTP local en loopback.')
        self.url = url.rstrip('/')
        self.modelo = modelo
        self.timeout = timeout
        self.transport = transport
        self._ocupado = asyncio.Semaphore(1)

    async def extraer(self, transcripcion: str):
        captura = await self.extraer_estructurado(
            transcripcion, PROMPT_EXTRACCION, CapturaModelo
        )
        return validar_propuesta(captura.propuestas(), transcripcion)

    async def extraer_estructurado(
        self, transcripcion: str, prompt: str, modelo_respuesta: type[TRespuesta],
        esquema: dict | None = None,
    ) -> TRespuesta:
        try:
            await asyncio.wait_for(self._ocupado.acquire(), timeout=0.1)
        except TimeoutError:
            raise ErrorExtractor('El extractor está ocupado. Espera y vuelve a intentarlo.') from None
        try:
            async with asyncio.timeout(self.timeout):
                async with httpx.AsyncClient(timeout=self.timeout, trust_env=False,
                        follow_redirects=False, transport=self.transport) as client:
                    async with client.stream('POST', f'{self.url}/api/chat', json={
                        'model': self.modelo, 'stream': False,
                        'format': esquema or modelo_respuesta.model_json_schema(),
                        'messages': [{'role': 'system', 'content': prompt},
                                     {'role': 'user', 'content': transcripcion}],
                        'options': {'temperature': 0, 'num_ctx': 8192, 'num_predict': 2400},
                        'keep_alive': '2m',
                    }) as response:
                        response.raise_for_status()
                        data = bytearray()
                        async for chunk in response.aiter_bytes():
                            data.extend(chunk)
                            if len(data) > 128000:
                                raise ValueError('Respuesta excesiva')
            payload = json.loads(data)
            if (not isinstance(payload, dict) or not isinstance(payload.get('message'), dict)
                    or not isinstance(payload['message'].get('content'), str)):
                raise ValueError('Contrato de respuesta no válido')
            contenido = payload['message']['content'].strip()
            # Recuperación controlada solo del envoltorio Markdown; no reparar contenido clínico.
            if contenido.startswith('```json\n') and contenido.endswith('```'):
                contenido = contenido[8:-3].strip()
            return modelo_respuesta.model_validate_json(contenido)
        except (httpx.HTTPError, TimeoutError):
            raise ErrorExtractor('El modelo local no está disponible o agotó su tiempo. Puedes continuar manualmente.') from None
        except (ValidationError, ValueError, KeyError, TypeError):
            raise ErrorExtractor('La salida del modelo no pudo validarse. Reintenta o continúa manualmente.') from None
        finally:
            self._ocupado.release()
