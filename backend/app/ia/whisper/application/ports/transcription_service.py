from typing import Protocol


class ServicioTranscripcion(Protocol):
    async def transcribir(self, audio_bytes: bytes) -> str: ...
