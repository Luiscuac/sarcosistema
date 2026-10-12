from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.ia.application.errors.transcription_error import ErrorTranscripcion
from app.ia.application.use_cases.transcribir_audio import TranscribirAudio
from app.ia.infrastructure.providers import proveer_transcribir_audio
from app.ia.presentation.schemas.transcription_response import TranscripcionResponse

router = APIRouter()

TAMANO_MAXIMO_AUDIO = 20 * 1024 * 1024
FORMATOS_AUDIO = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg", ".flac", ".mpeg"}


@router.post("/transcribir", response_model=TranscripcionResponse)
async def transcribir_audio(
    archivo: UploadFile = File(...),
    _usuario: Usuario = Depends(usuario_actual),
    caso_uso: TranscribirAudio = Depends(proveer_transcribir_audio),
) -> TranscripcionResponse:
    """Transcribe audio localmente; el resultado siempre requiere revisión humana."""
    nombre = (archivo.filename or "").lower()
    extension = "." + nombre.rsplit(".", 1)[-1] if "." in nombre else ""
    if extension not in FORMATOS_AUDIO:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Formato de audio no admitido.")

    audio = await archivo.read(TAMANO_MAXIMO_AUDIO + 1)
    await archivo.close()
    if not audio:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo de audio está vacío.")
    if len(audio) > TAMANO_MAXIMO_AUDIO:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "El audio supera el límite de 20 MB.")

    try:
        texto = await caso_uso.ejecutar(audio)
    except ErrorTranscripcion as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "El modelo local de transcripción no está disponible o no pudo procesar el audio.",
        ) from error
    return TranscripcionResponse(texto=texto)
