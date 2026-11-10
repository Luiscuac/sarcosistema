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
    PacienteNuevo, SolicitudNueva, TomaMuestraNueva, MuestraSolicitudNueva, IncidenciaNueva,
    IncidenciaSolicitudNueva, ValorResultadoEntrada,
)
from app.laboratorio.infrastructure.persistence.repository import SqlAlchemyExamenRepository
from app.laboratorio.presentation.schemas import (
    CrearPacienteRequest,
    CrearSolicitudRequest,
    EstudioCatalogoResponse,
    EstudioPendienteResponse,
    PacienteResponse,
    SolicitudCreadaResponse,
    SolicitudDetalleResponse,
    InformeSolicitudResponse,
    RecibirMuestraRequest,
    RecibirMuestraSolicitudRequest,
    ResultadoEstudioResponse,
    GuardarBorradorRequest,
    ResultadoAccionResponse,
    MuestraRecibidaResponse,
    RegistrarIncidenciaRequest,
    RegistrarIncidenciasSolicitudRequest,
    IncidenciasRegistradasResponse,
    IncidenciaResponse,
    PublicarResultadoRequest,
    GuardarBorradorAreaRequest,
    PublicarResultadosAreaRequest,
    ResultadoAreaAccionResponse,
    MedicoSolicitanteResponse,
)

router = APIRouter(
    prefix="/laboratorio",
    tags=["laboratorio"],
    dependencies=[Depends(requiere_rol("laboratorio"))],
)

router_medico = APIRouter(
    prefix="/laboratorio",
    tags=["laboratorio"],
    dependencies=[Depends(requiere_rol("medico"))],
)


def get_service(db: AsyncSession = Depends(get_db)) -> LaboratorioService:
    return LaboratorioService(SqlAlchemyExamenRepository(db))


@router_medico.get("/pacientes/{paciente_id}/solicitudes", response_model=list[SolicitudDetalleResponse])
async def solicitudes_del_paciente(
    paciente_id: int,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    return await service.listar_solicitudes_paciente(paciente_id, usuario.id)


@router_medico.get("/medicos/solicitudes/{solicitud_id}/informe", response_model=InformeSolicitudResponse)
async def obtener_informe_medico(
    solicitud_id: int,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        informe = await service.obtener_informe_medico(solicitud_id, usuario.id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    if informe is None:
        raise HTTPException(status_code=404, detail="El informe no está disponible")
    return informe


@router.get("/medicos", response_model=list[MedicoSolicitanteResponse])
async def listar_medicos(
    termino: str = Query(min_length=2, max_length=100),
    service: LaboratorioService = Depends(get_service),
):
    return await service.listar_medicos(termino)


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
        telefono=data.telefono,
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
    enviados = data.model_dump(exclude_unset=True)
    solicitud = SolicitudNueva(
        paciente_id=data.paciente_id,
        tipo_estudio_ids=tuple(data.tipo_estudio_ids),
        fecha_solicitud=data.fecha_solicitud,
        referencia_papel_formulario=data.referencia_papel_formulario,
        establecimiento_solicitante_nombre=data.establecimiento_solicitante_nombre,
        procedencia=data.procedencia,
        medico_solicitante_nombre=data.medico_solicitante_nombre,
        medico_solicitante_id=data.medico_solicitante_id,
        diagnostico_principal=data.diagnostico_principal,
        prioridad=data.prioridad,
        clave_idempotencia=str(data.clave_idempotencia),
        fecha_solicitud_explicita='fecha_solicitud' in enviados,
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


@router.get("/solicitudes/{solicitud_id}", response_model=SolicitudDetalleResponse)
async def obtener_solicitud(
    solicitud_id: int,
    service: LaboratorioService = Depends(get_service),
):
    solicitud = await service.obtener_solicitud(solicitud_id)
    if solicitud is None:
        raise HTTPException(status_code=404, detail="La solicitud no existe")
    return solicitud


@router.get("/solicitudes/{solicitud_id}/informe", response_model=InformeSolicitudResponse)
async def obtener_informe(
    solicitud_id: int,
    service: LaboratorioService = Depends(get_service),
):
    try:
        informe = await service.obtener_informe(solicitud_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    if informe is None:
        raise HTTPException(status_code=404, detail="La solicitud no existe")
    return informe


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
                responsable_recepcion=data.responsable_recepcion,
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
                responsable_recepcion=data.responsable_recepcion,
            ),
            usuario.id,
        )
        return MuestraRecibidaResponse(referencia_muestra=referencia)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.post(
    "/solicitudes/{solicitud_id}/incidencias",
    response_model=IncidenciasRegistradasResponse,
    status_code=201,
)
async def registrar_incidencias_solicitud(
    solicitud_id: int,
    data: RegistrarIncidenciasSolicitudRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        cantidad = await service.registrar_incidencias_solicitud(
            IncidenciaSolicitudNueva(
                solicitud_id, tuple(data.estudio_ids), data.motivo, data.descripcion, data.responsable,
            ),
            usuario.id,
        )
        return IncidenciasRegistradasResponse(cantidad=cantidad)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.post("/estudios/{estudio_id}/incidencias", response_model=IncidenciaResponse, status_code=201)
async def registrar_incidencia(
    estudio_id: int,
    data: RegistrarIncidenciaRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        return await service.registrar_incidencia(
            IncidenciaNueva(estudio_id, data.motivo, data.descripcion, data.responsable),
            usuario.id,
        )
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
            data.responsable_analisis,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.post(
    "/estudios/{estudio_id}/resultado/publicar",
    response_model=ResultadoAccionResponse,
)
async def publicar_resultado(
    estudio_id: int,
    data: PublicarResultadoRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        return await service.publicar_resultado(estudio_id, usuario.id, data.responsable_publicacion)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.put(
    "/solicitudes/{solicitud_id}/areas/{area_codigo}/resultados/borrador",
    response_model=ResultadoAreaAccionResponse,
)
async def guardar_borrador_area(
    solicitud_id: int,
    area_codigo: str,
    data: GuardarBorradorAreaRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        estudios = tuple((
            item.estudio_id,
            tuple(ValorResultadoEntrada(**valor.model_dump()) for valor in item.valores),
        ) for item in data.estudios)
        resultados = await service.guardar_borrador_area(
            solicitud_id, area_codigo, estudios, data.observaciones, usuario.id, data.responsable,
        )
        return {"cantidad": len(resultados), "estado": "borrador"}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.post(
    "/solicitudes/{solicitud_id}/areas/{area_codigo}/resultados/publicar",
    response_model=ResultadoAreaAccionResponse,
)
async def publicar_resultados_area(
    solicitud_id: int,
    area_codigo: str,
    data: PublicarResultadosAreaRequest,
    usuario: Usuario = Depends(usuario_actual),
    service: LaboratorioService = Depends(get_service),
):
    try:
        resultados = await service.publicar_resultados_area(
            solicitud_id, area_codigo, tuple(data.estudio_ids), usuario.id, data.responsable,
        )
        return {"cantidad": len(resultados), "estado": "publicado"}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
