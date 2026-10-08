"""
Consultas especificas a la BD del modulo laboratorio.
Equivalente a resultado.repository.ts: si no se usa el ORM directo en el service.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.laboratorio.domain.entities import Examen as ExamenDomain
from app.laboratorio.infrastructure.persistence.models import Examen as ExamenModel


class SqlAlchemyExamenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear(self, examen: ExamenDomain) -> ExamenDomain:
        modelo = ExamenModel(paciente_id=examen.paciente_id, tipo=examen.tipo)
        self.db.add(modelo)
        await self.db.flush()
        await self.db.refresh(modelo)
        return ExamenDomain(modelo.id, modelo.paciente_id, modelo.tipo, modelo.estado)

    async def obtener_por_id(self, examen_id: int) -> ExamenDomain | None:
        result = await self.db.execute(
            select(ExamenModel).where(ExamenModel.id == examen_id)
        )
        modelo = result.scalar_one_or_none()
        if modelo is None:
            return None
        return ExamenDomain(modelo.id, modelo.paciente_id, modelo.tipo, modelo.estado)
