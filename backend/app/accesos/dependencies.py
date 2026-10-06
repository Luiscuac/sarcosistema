"""
RBAC: verificacion de permisos como dependencia de FastAPI.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accesos/login")


def requiere_permiso(permiso: str):
    async def verificador(token: str = Depends(oauth2_scheme)):
        # TODO: decodificar token, revisar que el rol tenga el permiso dado
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Pendiente de implementar")
    return verificador
