"""Contrato HTTP de la transcripción local: formatos, tamaños, autorización y fallos.

El modelo NO se descarga: el caso de uso se sustituye por un doble.
"""
import pytest

from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.ia.whisper.application.errors.transcription_error import ErrorTranscripcion
from app.ia.whisper.application.use_cases.transcribir_audio import TranscribirAudio
from app.ia.whisper.infrastructure.providers import proveer_transcribir_audio
from app.ia.whisper.presentation.routes import transcription as rutas_transcripcion
from app.main import app


class CasoUsoDoble:
    def __init__(self, texto="Paciente refiere tos ficticia.", error=None):
        self.texto = texto
        self.error = error
        self.recibido = None

    async def ejecutar(self, audio):
        self.recibido = audio
        if self.error:
            raise self.error
        return self.texto


@pytest.fixture
def caso_uso():
    doble = CasoUsoDoble()
    app.dependency_overrides[proveer_transcribir_audio] = lambda: doble
    yield doble
    app.dependency_overrides.pop(proveer_transcribir_audio, None)


@pytest.fixture
def con_sesion(usuarios):
    app.dependency_overrides[usuario_actual] = lambda: usuarios
    yield
    app.dependency_overrides.pop(usuario_actual, None)


@pytest.mark.asyncio
async def test_transcribe_audio_valido_y_devuelve_texto(client, caso_uso, con_sesion):
    respuesta = await client.post(
        "/ia/transcribir",
        files={"archivo": ("grabacion.webm", b"audio-ficticio", "audio/webm")},
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["texto"] == "Paciente refiere tos ficticia."
    assert caso_uso.recibido == b"audio-ficticio"


@pytest.mark.asyncio
async def test_requiere_sesion(client, caso_uso):
    respuesta = await client.post(
        "/ia/transcribir",
        files={"archivo": ("grabacion.webm", b"audio-ficticio", "audio/webm")},
    )
    assert respuesta.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("nombre", ["informe.txt", "imagen.png", "sin_extension"])
async def test_formato_no_admitido_devuelve_415(client, caso_uso, con_sesion, nombre):
    respuesta = await client.post("/ia/transcribir", files={"archivo": (nombre, b"datos", "text/plain")})
    assert respuesta.status_code == 415
    assert caso_uso.recibido is None


@pytest.mark.asyncio
async def test_archivo_vacio_devuelve_400(client, caso_uso, con_sesion):
    respuesta = await client.post(
        "/ia/transcribir", files={"archivo": ("grabacion.webm", b"", "audio/webm")}
    )
    assert respuesta.status_code == 400
    assert caso_uso.recibido is None


@pytest.mark.asyncio
async def test_audio_demasiado_grande_devuelve_413(client, caso_uso, con_sesion, monkeypatch):
    monkeypatch.setattr(rutas_transcripcion, "TAMANO_MAXIMO_AUDIO", 4)
    respuesta = await client.post(
        "/ia/transcribir", files={"archivo": ("grabacion.webm", b"audio-largo-ficticio", "audio/webm")}
    )
    assert respuesta.status_code == 413
    assert caso_uso.recibido is None


@pytest.mark.asyncio
async def test_fallo_del_modelo_es_recuperable_y_no_revela_detalles(client, con_sesion):
    doble = CasoUsoDoble(error=ErrorTranscripcion("fallo interno del provingedor ficticio"))
    app.dependency_overrides[proveer_transcribir_audio] = lambda: doble
    try:
        respuesta = await client.post(
            "/ia/transcribir", files={"archivo": ("grabacion.webm", b"audio-ficticio", "audio/webm")}
        )
    finally:
        app.dependency_overrides.pop(proveer_transcribir_audio, None)
    assert respuesta.status_code == 503
    assert "provingedor" not in respuesta.text


async def test_errores_inesperados_se_envuelven_como_error_de_transcripcion():
    class ServicioRoto:
        async def transcribir(self, audio):
            raise RuntimeError("detalle técnico que no debe filtrarse")

    with pytest.raises(ErrorTranscripcion):
        await TranscribirAudio(ServicioRoto()).ejecutar(b"audio")


async def test_error_de_transcripcion_se_propaga_sin_reenvolver():
    original = ErrorTranscripcion("ya envuelto")

    class ServicioRoto:
        async def transcribir(self, audio):
            raise original

    with pytest.raises(ErrorTranscripcion) as detalle:
        await TranscribirAudio(ServicioRoto()).ejecutar(b"audio")
    assert detalle.value is original
