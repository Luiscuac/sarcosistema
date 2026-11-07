from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.accesos.presentation.dependencies.role_required import requiere_rol
from app.config.database import get_db
from app.enfermeria.application.use_cases.registrar_admision import RegistrarAdmision
from app.enfermeria.infrastructure.persistence.repository import SqlAlchemyRegistroEnfermeriaRepository
from app.enfermeria.presentation.schemas import AdmisionRequest

router = APIRouter(prefix='/enfermeria', tags=['enfermeria'])


def get_repository(db: AsyncSession = Depends(get_db)):
    return SqlAlchemyRegistroEnfermeriaRepository(db)


@router.get('/pacientes', dependencies=[Depends(requiere_rol('enfermeria'))])
async def buscar_pacientes(
    buscar: str = Query(min_length=2, max_length=100),
    pagina: int = Query(default=1, ge=1),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    return await repo.buscar_pacientes(buscar.strip(), pagina, 20)


@router.post('/pacientes/{paciente_id}/registros', status_code=201,
             dependencies=[Depends(requiere_rol('enfermeria'))])
async def crear_borrador(
    paciente_id: int,
    datos: AdmisionRequest,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    try:
        return await RegistrarAdmision(repo).ejecutar(paciente_id, usuario.id, datos)
    except LookupError:
        raise HTTPException(404, 'Paciente no encontrado.') from None


@router.get('/pacientes/{paciente_id}/registros',
            dependencies=[Depends(requiere_rol('enfermeria'))])
async def listar_registros_enfermeria(
    paciente_id: int,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    if await repo.obtener_paciente(paciente_id) is None:
        raise HTTPException(404, 'Paciente no encontrado.')
    return await repo.listar_registros(paciente_id, usuario.id)


@router.put('/registros/{registro_id}', dependencies=[Depends(requiere_rol('enfermeria'))])
async def editar_borrador(
    registro_id: int,
    datos: AdmisionRequest,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    resultado = await repo.editar_borrador(registro_id, usuario.id, datos)
    if resultado is None:
        raise HTTPException(409, 'El borrador no existe, no te pertenece o ya fue publicado.')
    return resultado


@router.post('/registros/{registro_id}/publicar',
             dependencies=[Depends(requiere_rol('enfermeria'))])
async def publicar_registro(
    registro_id: int,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    resultado = await repo.publicar(registro_id, usuario.id)
    if resultado is None:
        raise HTTPException(409, 'El borrador no existe, no te pertenece o ya fue publicado.')
    return resultado


@router.get('/pacientes/{paciente_id}/publicados',
            dependencies=[Depends(requiere_rol('medico'))])
async def listar_publicados_para_medico(
    paciente_id: int,
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    if await repo.obtener_paciente(paciente_id) is None:
        raise HTTPException(404, 'Paciente no encontrado.')
    return await repo.listar_publicados(paciente_id)
