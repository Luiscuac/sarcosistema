from fastapi import APIRouter, Depends, HTTPException, status

from app.accesos.application.errors.invalid_credentials import CredencialesInvalidas
from app.accesos.application.use_cases.iniciar_sesion import IniciarSesion
from app.accesos.presentation.schemas.login_request import LoginRequest
from app.accesos.presentation.schemas.login_response import LoginResponse
from app.config.providers import proveer_inicio_sesion

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def iniciar_sesion(
    credenciales: LoginRequest,
    caso_uso: IniciarSesion = Depends(proveer_inicio_sesion),
) -> LoginResponse:
    try:
        sesion = await caso_uso.ejecutar(
            credenciales.identificador_acceso,
            credenciales.password,
        )
    except CredencialesInvalidas:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Credenciales incorrectas",
        ) from None

    return LoginResponse(access_token=sesion.access_token, token_type=sesion.token_type)
