from app.ia.whisper.application.errors.transcription_error import ErrorTranscripcion
from app.ia.whisper.application.ports.transcription_service import ServicioTranscripcion


class TranscribirAudio:
    def __init__(self, servicio: ServicioTranscripcion):
        self.servicio = servicio

    async def ejecutar(self, audio: bytes) -> str:
        try:
            return await self.servicio.transcribir(audio)
        except ErrorTranscripcion:
            raise
        except Exception as error:
            raise ErrorTranscripcion from error
