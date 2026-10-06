"""
Consultas especificas a la BD del modulo laboratorio.
Equivalente a resultado.repository.ts: si no se usa el ORM directo en el service.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.laboratorio.models import Examen


class ExamenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear(self, examen: Examen) -> Examen:
        self.db.add(examen)
        await self.db.commit()
        await self.db.refresh(examen)
        return examen

    async def obtener_por_id(self, examen_id: int) -> Examen | None:
        result = await self.db.execute(select(Examen).where(Examen.id == examen_id))
        return result.scalar_one_or_none()
