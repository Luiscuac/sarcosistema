from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from functools import lru_cache

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.accesos.presentation.dependencies.role_required import requiere_rol
from app.config.database import get_db
from app.consultas.application.use_cases.consultar_historial import ConsultarHistorial
from app.consultas.application.use_cases.consultar_pacientes import ConsultarPacientes
from app.consultas.application.use_cases.registrar_consulta import RegistrarConsulta
from app.consultas.infrastructure.persistence.repository import SqlAlchemyConsultaRepository
from app.consultas.presentation.schemas import ConsultaNueva
from app.consultas.presentation.schemas import ExtraerDatosRequest
from app.consultas.application.use_cases.extraer_datos_clinicos import ExtraerDatosClinicos
from app.consultas.application.ports.extractor_clinico import ErrorExtractor
from app.consultas.infrastructure.ia.ollama import OllamaExtractor
from app.config.settings import settings
from app.imagenes.application.use_cases.solicitar_ecografia import SolicitarEcografia
from app.imagenes.domain.errors import SolicitudInvalida
from app.imagenes.infrastructure.persistence.repository import RepositorioImagenSql
from app.imagenes.presentation.schemas import (
    EstudioPublicadoResponse,
    SolicitudEcografiaRequest,
    SolicitudEcografiaResponse,
)

router = APIRouter(prefix='/consultas', tags=['consultas'], dependencies=[Depends(requiere_rol('medico'))])


def get_repository(db: AsyncSession = Depends(get_db)) -> SqlAlchemyConsultaRepository:
    return SqlAlchemyConsultaRepository(db)


def get_repositorio_imagen(db: AsyncSession = Depends(get_db)) -> RepositorioImagenSql:
    return RepositorioImagenSql(db)


@lru_cache
def get_extractor():
    if not settings.clinical_extractor_enabled:
        raise HTTPException(503, 'El autocompletado no está habilitado. Puedes continuar manualmente.')
    try:
        return OllamaExtractor(settings.ollama_url, settings.ollama_model,
                               settings.clinical_extractor_timeout_seconds)
    except ValueError:
        raise HTTPException(503, 'La configuración del extractor local no es válida.') from None


@router.post('/extraer-datos-clinicos')
async def extraer_datos_clinicos(
    datos: ExtraerDatosRequest,
    repo: SqlAlchemyConsultaRepository = Depends(get_repository),
    extractor=Depends(get_extractor),
):
    try:
        return await ExtraerDatosClinicos(repo, extractor).ejecutar(datos.paciente_id, datos.transcripcion)
    except LookupError:
        raise HTTPException(404, 'Paciente no encontrado.') from None
    except ErrorExtractor:
        raise HTTPException(503, 'No se pudo analizar con el modelo local. Reintenta o continúa manualmente.') from None


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
    repo_imagen: RepositorioImagenSql = Depends(get_repositorio_imagen),
):
    resultado = await ConsultarHistorial(repo).ejecutar(paciente_id, pagina, limite)
    if resultado is None:
        raise HTTPException(404, 'Paciente no encontrado.')
    # Examenes complementarios del paciente: solo los estudios publicados.
    resultado['estudios_imagen'] = [
        EstudioPublicadoResponse.model_validate(estudio)
        for estudio in await repo_imagen.listar_publicados_paciente(paciente_id)
    ]
    return resultado


@router.post('/estudios-imagen', status_code=201, response_model=SolicitudEcografiaResponse)
async def solicitar_ecografia(
    datos: SolicitudEcografiaRequest,
    usuario: Usuario = Depends(usuario_actual),
    repo_imagen: RepositorioImagenSql = Depends(get_repositorio_imagen),
):
    try:
        datos.validar_estudios()
        solicitud_id = await SolicitarEcografia(repo_imagen).ejecutar(
            datos.modelo_solicitud(), usuario.id
        )
    except (SolicitudInvalida, ValueError) as exc:
        raise HTTPException(422, str(exc)) from None
    return SolicitudEcografiaResponse(solicitud_id=solicitud_id, estudios=datos.tipo_estudio_ids)


@router.get('/catalogo-imagenes')
async def catalogo_imagenes(
    modalidad: str = Query(default='ecografia', pattern='^(ecografia|rayos_x)$'),
    repo_imagen: RepositorioImagenSql = Depends(get_repositorio_imagen),
):
    """Tipos activos de ecografía o Rayos X que el médico puede solicitar."""
    if modalidad == 'ecografia':
        return await repo_imagen.listar_catalogo_imagen()
    return await repo_imagen.listar_catalogo_imagen(modalidad)


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
