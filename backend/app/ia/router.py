"""Endpoints de asistencia experimental con IA."""

from functools import lru_cache

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.config.settings import settings
from app.ia.transcripcion import ErrorTranscripcion, TranscripcionService

router = APIRouter(prefix="/ia", tags=["ia"])

TAMANO_MAXIMO_AUDIO = 20 * 1024 * 1024
FORMATOS_AUDIO = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg", ".flac", ".mpeg"}


@lru_cache(maxsize=1)
def obtener_servicio_transcripcion() -> TranscripcionService:
    return TranscripcionService(
        model_size=settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        model_dir=settings.whisper_model_dir,
        cpu_threads=settings.whisper_cpu_threads,
    )


class TranscripcionResponse(BaseModel):
    texto: str
    requiere_revision: bool = True


@router.post("/transcribir", response_model=TranscripcionResponse)
async def transcribir_audio(
    archivo: UploadFile = File(...),
    _usuario: Usuario = Depends(usuario_actual),
) -> TranscripcionResponse:
    """Transcribe audio localmente con faster-whisper; requiere revisión humana."""
    nombre = (archivo.filename or "").lower()
    extension = "." + nombre.rsplit(".", 1)[-1] if "." in nombre else ""
    if extension not in FORMATOS_AUDIO:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Formato de audio no admitido.",
        )

    audio = await archivo.read(TAMANO_MAXIMO_AUDIO + 1)
    await archivo.close()
    if not audio:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo de audio está vacío.")
    if len(audio) > TAMANO_MAXIMO_AUDIO:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "El audio supera el límite de 20 MB.")

    try:
        texto = await obtener_servicio_transcripcion().transcribir(audio)
    except ErrorTranscripcion as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "El modelo local de transcripción no está disponible o no pudo procesar el audio.",
        ) from error

    return TranscripcionResponse(texto=texto)
