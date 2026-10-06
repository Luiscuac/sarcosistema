"""
Integracion con Whisper.cpp (voz a texto) y Ollama (LLM local) corriendo
en el servidor local del hospital, segun la decision de privacidad total
sin servicios externos de pago.
"""


class TranscripcionService:
    async def transcribir(self, audio_bytes: bytes) -> str:
        """Llama al binario/servicio local de whisper.cpp."""
        raise NotImplementedError

    async def asistir_redaccion(self, texto_transcrito: str) -> str:
        """Llama a Ollama local para proponer redaccion del informe/receta."""
        raise NotImplementedError
