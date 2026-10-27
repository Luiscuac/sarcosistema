from typing import Protocol

from app.consultas.domain.entities import MedicoVigente


class ConsultaRepository(Protocol):
    async def medico_vigente(self, usuario_id: int) -> MedicoVigente | None: ...
    async def crear(self, datos, usuario_id: int, medico: MedicoVigente) -> tuple[dict, bool]: ...
