"""Endpoints iniciales de paciente, catálogo y bandeja del laboratorio."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.accesos.presentation.dependencies.role_required import requiere_rol
from app.config.database import get_db
from app.laboratorio.application.use_cases.service import LaboratorioService
from app.laboratorio.domain.entities import (
    PacienteNuevo, SolicitudNueva, TomaMuestraNueva, MuestraSolicitudNueva, ValorResultadoEntrada,
)
from app.laboratorio.infrastructure.persistence.repository import SqlAlchemyExamenRepository
from app.laboratorio.presentation.schemas import (
    CrearPacienteRequest,
    CrearSolicitudRequest,
    EstudioCatalogoResponse,
    EstudioPendienteResponse,
    PacienteResponse,
    SolicitudCreadaResponse,
    RecibirMuestraRequest,
    RecibirMuestraSolicitudRequest,
    ResultadoEstudioResponse,
    GuardarBorradorRequest,
    ResultadoAccionResponse,
    MuestraRecibidaResponse,
)

router = APIRouter(
    prefix="/laboratorio",
    tags=["laboratorio"],
    dependencies=[Depends(requiere_rol("laboratorio"))],
)


def get_service(db: AsyncSession = Depends(get_db)) -> LaboratorioService:
    return LaboratorioService(SqlAlchemyExamenRepository(db))


@router.get("/catalogo/estudios", response_model=list[EstudioCatalogoResponse])
async def listar_catalogo(service: LaboratorioService = Depends(get_service)):
    return await service.listar_catalogo()


@router.get("/estudios/pendientes", response_model=list[EstudioPendienteResponse])
async def listar_pendientes(service: LaboratorioService = Depends(get_service)):
    return await service.listar_pendientes()


@router.get("/estudios/publicados", response_model=list[EstudioPendienteResponse])
async def listar_publicados(service: LaboratorioService = Depends(get_service)):
    return await service.listar_publicados()


@router.get("/pacientes", response_model=list[PacienteResponse])
async def buscar_pacientes(
    termino: str = Query(min_length=2, max_length=100),
    service: LaboratorioService = Depends(get_service),
):
    return await service.buscar_pacientes(termino)


@router.post(
    "/pacientes",
    response_model=PacienteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_paciente(
    data: CrearPacienteRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    paciente = PacienteNuevo(
        nombre_completo=data.nombre_completo,
        fecha_nacimiento=data.fecha_nacimiento,
        sexo=data.sexo,
        tipo_documento=data.tipo_documento,
        numero_documento=data.numero_documento,
        sin_documento=data.sin_documento,
        historia_clinica=data.historia_clinica,
        codigo_externo=data.codigo_externo,
    )
    try:
        return await service.crear_paciente(paciente, usuario.id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un paciente con ese tipo y número de documento.",
        ) from None


@router.post(
    "/solicitudes",
    response_model=SolicitudCreadaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_solicitud(
    data: CrearSolicitudRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    solicitud = SolicitudNueva(
        paciente_id=data.paciente_id,
        tipo_estudio_ids=tuple(data.tipo_estudio_ids),
        fecha_solicitud=data.fecha_solicitud,
        referencia_papel_formulario=data.referencia_papel_formulario,
        establecimiento_solicitante_nombre=data.establecimiento_solicitante_nombre,
        medico_solicitante_nombre=data.medico_solicitante_nombre,
        diagnostico_principal=data.diagnostico_principal,
        prioridad=data.prioridad,
        clave_idempotencia=str(data.clave_idempotencia),
    )
    try:
        return await service.crear_solicitud(solicitud, usuario.id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud se recibió duplicada. Actualiza la bandeja antes de reintentar.",
        ) from None


@router.post(
    "/solicitudes/{solicitud_id}/muestras",
    response_model=MuestraRecibidaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def recibir_muestra_solicitud(
    solicitud_id: int,
    data: RecibirMuestraSolicitudRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        referencia = await service.recibir_muestra_solicitud(
            MuestraSolicitudNueva(
                solicitud_id=solicitud_id,
                estudio_ids=tuple(data.estudio_ids),
                tipo_muestra=data.tipo_muestra,
                fecha_toma=data.fecha_toma,
                hora_toma=data.hora_toma,
                hora_no_registrada=data.hora_no_registrada,
            ),
            usuario.id,
        )
        return MuestraRecibidaResponse(referencia_muestra=referencia)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.post(
    "/estudios/{estudio_id}/muestra",
    response_model=MuestraRecibidaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def recibir_muestra(
    estudio_id: int,
    data: RecibirMuestraRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        referencia = await service.recibir_muestra(
            TomaMuestraNueva(
                estudio_id=estudio_id,
                tipo_muestra=data.tipo_muestra,
                fecha_toma=data.fecha_toma,
                hora_toma=data.hora_toma,
                hora_no_registrada=data.hora_no_registrada,
            ),
            usuario.id,
        )
        return MuestraRecibidaResponse(referencia_muestra=referencia)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.get(
    "/estudios/{estudio_id}/resultado",
    response_model=ResultadoEstudioResponse,
)
async def obtener_resultado(
    estudio_id: int,
    service: LaboratorioService = Depends(get_service),
):
    try:
        return await service.obtener_resultado(estudio_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None


@router.put(
    "/estudios/{estudio_id}/resultado/borrador",
    response_model=ResultadoAccionResponse,
)
async def guardar_borrador(
    estudio_id: int,
    data: GuardarBorradorRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        return await service.guardar_borrador(
            estudio_id,
            tuple(ValorResultadoEntrada(**item.model_dump()) for item in data.valores),
            data.observaciones,
            usuario.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.post(
    "/estudios/{estudio_id}/resultado/publicar",
    response_model=ResultadoAccionResponse,
)
async def publicar_resultado(
    estudio_id: int,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        return await service.publicar_resultado(estudio_id, usuario.id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
