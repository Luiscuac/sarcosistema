from fastapi import Depends, HTTPException, status

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual


def requiere_rol(rol: str):
    async def verificar_rol(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol != rol:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin acceso a este módulo")
        return usuario

    return verificar_rol
