from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.accesos.presentation.dependencies.role_required import requiere_rol
from app.config.database import get_db
from app.consultas.application.use_cases.consultar_historial import ConsultarHistorial
from app.consultas.application.use_cases.consultar_pacientes import ConsultarPacientes
from app.consultas.application.use_cases.registrar_consulta import RegistrarConsulta
from app.consultas.infrastructure.persistence.repository import SqlAlchemyConsultaRepository
from app.consultas.presentation.schemas import ConsultaNueva

router = APIRouter(prefix='/consultas', tags=['consultas'], dependencies=[Depends(requiere_rol('medico'))])


def get_repository(db: AsyncSession = Depends(get_db)) -> SqlAlchemyConsultaRepository:
    return SqlAlchemyConsultaRepository(db)


@router.get('/pacientes')
async def buscar_pacientes(
    buscar: str = Query(min_length=2, max_length=100),
    pagina: int = Query(default=1, ge=1), limite: int = Query(default=20, ge=1, le=30),
    repo: SqlAlchemyConsultaRepository = Depends(get_repository),
):
    try:
        return await ConsultarPacientes(repo).ejecutar(buscar, pagina, limite)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


@router.get('/pacientes/{paciente_id}')
async def obtener_paciente(paciente_id: int, repo: SqlAlchemyConsultaRepository = Depends(get_repository)):
    paciente = await repo.obtener_paciente(paciente_id)
    if paciente is None:
        raise HTTPException(404, 'Paciente no encontrado.')
    return paciente


@router.get('/pacientes/{paciente_id}/historial')
async def historial(
    paciente_id: int, pagina: int = Query(default=1, ge=1),
    limite: int = Query(default=20, ge=1, le=30),
    repo: SqlAlchemyConsultaRepository = Depends(get_repository),
):
    resultado = await ConsultarHistorial(repo).ejecutar(paciente_id, pagina, limite)
    if resultado is None:
        raise HTTPException(404, 'Paciente no encontrado.')
    return resultado


@router.get('/{consulta_id}')
async def obtener_consulta(consulta_id: int, repo: SqlAlchemyConsultaRepository = Depends(get_repository)):
    consulta = await repo.obtener_consulta(consulta_id)
    if consulta is None:
        raise HTTPException(404, 'Consulta no encontrada.')
    return consulta


@router.post('', status_code=201)
async def registrar_consulta(
    datos: ConsultaNueva, response: Response,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyConsultaRepository = Depends(get_repository),
):
    try:
        detalle, nuevo = await RegistrarConsulta(repo).ejecutar(datos, usuario.id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from None
    except FileExistsError as exc:
        raise HTTPException(409, str(exc)) from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    if not nuevo:
        response.status_code = 200
    return detalle
