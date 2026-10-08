"""Inicio de sesión y comprobación de la sesión vigente."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.dependencies import usuario_actual
from app.accesos.repository import buscar_usuario
from app.accesos.security import crear_token, verificar_password
from app.config.database import get_db
from app.config.settings import settings

router = APIRouter(prefix="/accesos", tags=["accesos"])


class Credenciales(BaseModel):
    identificador_acceso: str
    password: str


@router.post("/login")
async def login(credenciales: Credenciales, db: AsyncSession = Depends(get_db)):
    usuario = await buscar_usuario(db, credenciales.identificador_acceso)
    if (
        not usuario
        or usuario["estado"] != "activo"
        or not usuario["rol_activo"]
        or usuario["trabajador_estado"] != "activo"
        or not verificar_password(credenciales.password, usuario["contrasena_hash"])
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales incorrectas")

    return {
        "access_token": crear_token(str(usuario["id"]), usuario["rol"], settings.jwt_secret_key),
        "token_type": "bearer",
    }


@router.get("/yo")
async def yo(usuario: dict = Depends(usuario_actual)):
    return {
        "id": usuario["id"],
        "identificador_acceso": usuario["identificador_acceso"],
        "rol": usuario["rol"],
    }
