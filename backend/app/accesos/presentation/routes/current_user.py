from fastapi import APIRouter, Depends

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.accesos.presentation.schemas.current_user_response import CurrentUserResponse

router = APIRouter()


@router.get("/yo", response_model=CurrentUserResponse)
async def obtener_perfil(usuario: Usuario = Depends(usuario_actual)) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=usuario.id,
        identificador_acceso=usuario.identificador_acceso,
        rol=usuario.rol,
    )
