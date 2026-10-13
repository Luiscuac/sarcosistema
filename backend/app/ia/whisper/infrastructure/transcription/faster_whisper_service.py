import asyncio
from functools import cached_property
from io import BytesIO
from threading import Lock

from faster_whisper import WhisperModel

from backend.app.ia.whisper.application.errors.transcription_error import ErrorTranscripcion


class FasterWhisperService:
    def __init__(
        self,
        model_size: str,
        device: str,
        compute_type: str,
        model_dir: str,
        cpu_threads: int,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model_dir = model_dir
        self.cpu_threads = cpu_threads
        self._inference_lock = Lock()

    @cached_property
    def model(self) -> WhisperModel:
        return WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            download_root=self.model_dir,
            cpu_threads=self.cpu_threads,
        )

    async def transcribir(self, audio_bytes: bytes) -> str:
        try:
            return await asyncio.to_thread(self._transcribir_sync, audio_bytes)
        except Exception as error:
            raise ErrorTranscripcion(
                "faster-whisper no pudo cargar el modelo o transcribir el audio"
            ) from error

    def _transcribir_sync(self, audio_bytes: bytes) -> str:
        with self._inference_lock:
            texto = self._transcribir_con_filtro(audio_bytes, filtrar_voz=True)
            if texto:
                return texto

            # El VAD puede descartar voz baja o distante; reintenta el audio completo.
            return self._transcribir_con_filtro(audio_bytes, filtrar_voz=False)

    def _transcribir_con_filtro(self, audio_bytes: bytes, filtrar_voz: bool) -> str:
        segmentos, _ = self.model.transcribe(
            BytesIO(audio_bytes),
            language="es",
            task="transcribe",
            vad_filter=filtrar_voz,
        )
        return "".join(segmento.text for segmento in segmentos).strip()
