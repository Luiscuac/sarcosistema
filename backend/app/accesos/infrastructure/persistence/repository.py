"""Implementación SQLAlchemy del puerto de repositorio de usuarios."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.infrastructure.persistence.mappers import mapear_usuario


class SqlAlchemyUsuarioRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def buscar_por_identificador(self, identificador: str) -> Usuario | None:
        result = await self.session.execute(
            text("""
                SELECT u.id, u.identificador_acceso, u.contrasena_hash,
                       u.estado, r.codigo AS rol, r.activo AS rol_activo,
                       t.estado AS trabajador_estado
                FROM public.usuario AS u
                JOIN public.rol AS r ON r.id = u.rol_id
                JOIN public.trabajador AS t ON t.id = u.trabajador_id
                WHERE u.identificador_acceso = :identificador
            """),
            {"identificador": identificador},
        )
        return mapear_usuario(result.mappings().one_or_none(), incluir_hash=True)

    async def buscar_por_id(self, usuario_id: int) -> Usuario | None:
        result = await self.session.execute(
            text("""
                SELECT u.id, u.identificador_acceso, u.estado,
                       r.codigo AS rol, r.activo AS rol_activo,
                       t.estado AS trabajador_estado
                FROM public.usuario AS u
                JOIN public.rol AS r ON r.id = u.rol_id
                JOIN public.trabajador AS t ON t.id = u.trabajador_id
                WHERE u.id = :usuario_id
            """),
            {"usuario_id": usuario_id},
        )
        return mapear_usuario(result.mappings().one_or_none())
