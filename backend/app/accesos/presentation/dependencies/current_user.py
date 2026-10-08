from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.accesos.application.errors.access_denied import AccesoNoAutorizado
from app.accesos.application.use_cases.obtener_usuario_actual import ObtenerUsuarioActual
from app.accesos.domain.entities import Usuario
from app.config.providers import proveer_usuario_actual

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accesos/login")


async def usuario_actual(
    token: str = Depends(oauth2_scheme),
    caso_uso: ObtenerUsuarioActual = Depends(proveer_usuario_actual),
) -> Usuario:
    try:
        return await caso_uso.ejecutar(token)
    except AccesoNoAutorizado:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Sesión inválida o vencida",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
