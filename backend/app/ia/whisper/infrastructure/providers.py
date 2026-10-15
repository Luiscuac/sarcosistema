from functools import lru_cache

from app.config.settings import settings
from app.ia.whisper.application.use_cases.transcribir_audio import TranscribirAudio
from app.ia.whisper.infrastructure.transcription.faster_whisper_service import FasterWhisperService


@lru_cache(maxsize=1)
def proveer_servicio_transcripcion() -> FasterWhisperService:
    return FasterWhisperService(
        model_size=settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        model_dir=settings.whisper_model_dir,
        cpu_threads=settings.whisper_cpu_threads,
    )


def proveer_transcribir_audio() -> TranscribirAudio:
    return TranscribirAudio(proveer_servicio_transcripcion())
