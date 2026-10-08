"""
Consultas especificas a la BD del modulo accesos.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.models import Usuario, Rol


class UsuarioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_por_identificador(self, identificador_acceso: str) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).where(Usuario.identificador_acceso == identificador_acceso)
        )
        return result.scalar_one_or_none()

    async def obtener_rol(self, rol_id: int) -> Rol | None:
        result = await self.db.execute(select(Rol).where(Rol.id == rol_id))
        return result.scalar_one_or_none()
