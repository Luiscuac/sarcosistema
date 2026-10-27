from fastapi import APIRouter, Depends, HTTPException

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.ia.transcriptor.application.use_cases.listar_registros_prueba import ListarRegistrosPrueba
from app.ia.transcriptor.infrastructure.registro_repository import RepositorioRegistrosPrueba
from app.ia.transcriptor.presentation.schemas.registro import RegistroPruebaResponse

router = APIRouter(prefix="/transcriptor", tags=["transcriptor"])


def proveer_caso_uso() -> ListarRegistrosPrueba:
    return ListarRegistrosPrueba(RepositorioRegistrosPrueba())


@router.get("/registros", response_model=list[RegistroPruebaResponse])
async def listar_registros(
    _usuario: Usuario = Depends(usuario_actual),
    caso_uso: ListarRegistrosPrueba = Depends(proveer_caso_uso),
):
    return caso_uso.ejecutar()


@router.get("/registros/{identificador}", response_model=RegistroPruebaResponse)
async def obtener_registro(
    identificador: str,
    _usuario: Usuario = Depends(usuario_actual),
    caso_uso: ListarRegistrosPrueba = Depends(proveer_caso_uso),
):
    registro = caso_uso.obtener(identificador)
    if registro is None:
        raise HTTPException(status_code=404, detail="Registro de prueba no encontrado.")
    return registro
