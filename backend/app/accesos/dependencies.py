"""Validación de sesión para rutas protegidas."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.repository import buscar_usuario_por_id
from app.accesos.security import ALGORITHM
from app.config.database import get_db
from app.config.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accesos/login")


def requiere_rol(rol: str):
    async def verificador(usuario: dict = Depends(usuario_actual)):
        if usuario["rol"] != rol:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin acceso a este módulo")
        return usuario
    return verificador


async def usuario_actual(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Sesión inválida o vencida",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        usuario_id = int(payload["sub"])
        if usuario_id <= 0:
            raise ValueError("invalid subject")
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise error from None

    usuario = await buscar_usuario_por_id(db, usuario_id)
    if (
        not usuario
        or usuario["estado"] != "activo"
        or not usuario["rol_activo"]
        or usuario["trabajador_estado"] != "activo"
    ):
        raise error
    return usuario
