"""Embeddings CPU: exclusivamente snapshot local verificado."""
import json
import hashlib
import math
import os
from pathlib import Path
import tempfile
import multiprocessing

from app.imagenes.infrastructure.vision.recursos import verificar_memoria, bloqueo_inferencia
from app.imagenes.domain.vision import ErrorVision, TiempoAgotado

MODEL_ID = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
DIMENSION = 384


def _worker_embeddings(conexion, directorio, minimo, textos, consulta):
    try:
        conexion.send(EmbeddingsLocales(directorio, minimo)._codificar_local(textos, consulta))
    except (ValueError, OSError, ErrorVision) as error:
        conexion.send(error)
    except Exception:
        conexion.send(ErrorVision('No se pudo ejecutar el modelo de embeddings local.'))
    finally:
        conexion.close()


def validar_vectores(vectores: list[list[float]]) -> list[list[float]]:
    for v in vectores:
        if len(v) != DIMENSION or not all(math.isfinite(x) for x in v):
            raise ValueError('Embedding de dimensión incompatible o no finito.')
        if not math.isclose(sum(x*x for x in v), 1., abs_tol=0.001):
            raise ValueError('Embedding debe tener norma unitaria.')
    return vectores


class EmbeddingsLocales:
    def __init__(self, directorio: Path, min_free_bytes: int = 2 * 1024**3):
        self.directorio = directorio
        self.min_free_bytes = min_free_bytes

    def codificar(self, textos: list[str], consulta: bool = False) -> list[list[float]]:
        # Las importaciones/modelo viven en un hijo para liberar también allocators
        # y memoria de bibliotecas entre indexación y consultas.
        self._validar_preparacion()
        verificar_memoria(self.min_free_bytes)
        contexto = multiprocessing.get_context('spawn')
        receptor, emisor = contexto.Pipe(duplex=False)
        proceso = contexto.Process(target=_worker_embeddings,
            args=(emisor, self.directorio, self.min_free_bytes, textos, consulta))
        try:
            proceso.start()
            emisor.close()
            if not receptor.poll(180):
                raise TiempoAgotado('Tiempo máximo de embeddings agotado.')
            try:
                resultado = receptor.recv()
            except EOFError:
                raise ErrorVision('El trabajador de embeddings terminó sin resultado.') from None
            if isinstance(resultado, Exception):
                raise resultado
            return validar_vectores(resultado)
        finally:
            emisor.close()
            receptor.close()
            if proceso.pid is not None:
                proceso.join(timeout=5)
                if proceso.is_alive():
                    proceso.terminate()
                    proceso.join(timeout=5)
                if proceso.is_alive():
                    proceso.kill()
                    proceso.join()
                proceso.close()

    def _validar_preparacion(self):
        manifiesto = self.directorio / 'manifest.json'
        if not manifiesto.is_file():
            raise ValueError('Modelo de embeddings no preparado; ejecutar preparación explícita.')
        manifest = json.loads(manifiesto.read_text(encoding='utf-8'))
        if manifest.get('model') != MODEL_ID or manifest.get('dimension') != DIMENSION:
            raise ValueError('Modelo de embeddings incompatible.')
        if not {'model.safetensors', 'config.json', 'tokenizer.json'} <= manifest.get('files', {}).keys():
            raise ValueError('Manifest de embeddings incompleto.')
        for nombre, sha in manifest['files'].items():
            archivo = (self.directorio / nombre).resolve()
            if not archivo.is_relative_to(self.directorio.resolve()):
                raise ValueError('Ruta de artefacto no permitida.')
            if archivo.stat().st_size > 1024**3:
                raise ValueError('Artefacto de embeddings excesivo.')
            with archivo.open('rb') as stream:
                obtenido = hashlib.file_digest(stream, 'sha256').hexdigest()
            if obtenido != sha:
                raise ValueError('Falló la integridad del modelo local.')

    def _codificar_local(self, textos: list[str], consulta: bool = False) -> list[list[float]]:
        self._validar_preparacion()
        if not textos or len(textos) > 256 or any(not t.strip() or len(t) > 4000 for t in textos):
            raise ValueError('Lote de textos vacío o excesivo.')
        verificar_memoria(self.min_free_bytes)
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        with bloqueo_inferencia(Path(tempfile.gettempdir())):
            import torch
            from sentence_transformers import SentenceTransformer
            torch.set_num_threads(2)
            modelo = SentenceTransformer(str(self.directorio), device='cpu', local_files_only=True,
                                        trust_remote_code=False, model_kwargs={'use_safetensors': True})
            try:
                modelo.max_seq_length = 128
                with torch.inference_mode():
                    vectores = modelo.encode(textos, batch_size=1, normalize_embeddings=True,
                                             show_progress_bar=False).tolist()
                return validar_vectores(vectores)
            finally:
                del modelo
