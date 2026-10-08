"""Composición de casos de uso con sus adaptadores concretos."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.application.use_cases.iniciar_sesion import IniciarSesion
from app.accesos.application.use_cases.obtener_usuario_actual import (
    ObtenerUsuarioActual,
)
from app.accesos.infrastructure.persistence.repository import SqlAlchemyUsuarioRepository
from app.accesos.infrastructure.security.jwt_service import JwtTokenService
from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import get_db
from app.config.settings import settings


def proveer_inicio_sesion(db: AsyncSession = Depends(get_db)) -> IniciarSesion:
    return IniciarSesion(
        SqlAlchemyUsuarioRepository(db),
        Argon2PasswordHasher(),
        JwtTokenService(settings.jwt_secret_key),
    )


def proveer_usuario_actual(db: AsyncSession = Depends(get_db)) -> ObtenerUsuarioActual:
    return ObtenerUsuarioActual(
        SqlAlchemyUsuarioRepository(db),
        JwtTokenService(settings.jwt_secret_key),
    )
