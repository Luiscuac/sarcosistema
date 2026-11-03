from typing import Protocol


class VisionTorax(Protocol):
    def analizar(self, contenido: bytes, proyeccion: str = 'PA', repeticiones: int = 1) -> dict: ...
