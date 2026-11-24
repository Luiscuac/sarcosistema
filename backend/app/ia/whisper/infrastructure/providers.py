from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import HTTPException

from app.config.settings import settings
from app.ia.whisper.application.use_cases.transcribir_audio import TranscribirAudio
if TYPE_CHECKING:
    from app.ia.whisper.infrastructure.transcription.faster_whisper_service import FasterWhisperService


@lru_cache(maxsize=1)
def proveer_servicio_transcripcion() -> 'FasterWhisperService':
    from app.ia.whisper.infrastructure.transcription.faster_whisper_service import FasterWhisperService

    return FasterWhisperService(
        model_size=settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        model_dir=settings.whisper_model_dir,
        cpu_threads=settings.whisper_cpu_threads,
        beam_size=settings.whisper_beam_size,
    )


def proveer_transcribir_audio() -> TranscribirAudio:
    if not settings.whisper_enabled:
        raise HTTPException(503, 'El dictado está deshabilitado en esta instalación.')
    return TranscribirAudio(proveer_servicio_transcripcion())
