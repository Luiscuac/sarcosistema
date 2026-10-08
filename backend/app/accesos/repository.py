"""Lecturas de identidad sobre las tablas existentes en database/schema.sql."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def buscar_usuario(db: AsyncSession, identificador: str):
    result = await db.execute(
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
    return result.mappings().one_or_none()


async def buscar_usuario_por_id(db: AsyncSession, usuario_id: int):
    result = await db.execute(
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
    return result.mappings().one_or_none()
