from typing import Protocol
from app.consultas.domain.extraccion import PropuestaClinica


class ErrorExtractor(Exception):
    """Error genérico seguro para presentación, sin texto clínico del proveedor."""


class ExtractorClinico(Protocol):
    modelo: str
    async def extraer(self, transcripcion: str) -> PropuestaClinica: ...
