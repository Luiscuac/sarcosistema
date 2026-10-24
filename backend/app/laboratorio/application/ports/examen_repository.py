from typing import Protocol

from app.laboratorio.domain.entities import Examen


class ExamenRepository(Protocol):
    async def crear(self, examen: Examen) -> Examen: ...

    async def obtener_por_id(self, examen_id: int) -> Examen | None: ...
