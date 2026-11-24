"""Endpoints del radiologo: bandeja, subida de imagenes/informe y publicacion."""
import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.config.database import get_db
from app.config.settings import settings
from app.imagenes.domain.ecografia import ORGANOS
from app.imagenes.application.use_cases.trabajar_estudio import (
    GuardarInforme,
    ListarBandeja,
    ObtenerEstudioImagen,
    PublicarInforme,
)
from app.imagenes.domain.errors import (
    ArchivoDemasiadoGrande,
    ArchivoNoEncontrado,
    ArchivoVacio,
    EstudioNoEncontrado,
    FormatoNoAdmitido,
    InformeSinContenido,
    InformeYaPublicado,
    SolicitudInvalida,
)
from app.imagenes.infrastructure.persistence.repository import RepositorioImagenSql
from app.imagenes.infrastructure.storage.almacen_local import AlmacenLocal
from app.imagenes.infrastructure.storage.almacen_s3 import AlmacenNoDisponible, AlmacenS3
from app.imagenes.presentation.schemas import (
    ArchivoImagenResponse,
    EstudioDetalleResponse,
    EstudioPendienteResponse,
    InformeImagenResponse,
    ResultadoAccionResponse,
    SolicitudEcografiaRequest,
)

# El prefijo /imagenes lo aplica app.imagenes.router (composición única del módulo).
router = APIRouter(tags=['imagenes'])

ROL_POR_MODALIDAD = {'ecografia': 'imagenes', 'rayos_x': 'rayos_x'}


def _validar_rol(usuario: Usuario, modalidad: str) -> None:
    if usuario.rol != ROL_POR_MODALIDAD[modalidad]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Sin acceso a esta área de imágenes.')


def _estudio_de_modalidad(estudio, modalidad: str) -> bool:
    nombre = estudio.tipo_estudio_nombre.casefold()
    return nombre.startswith('ecograf') if modalidad == 'ecografia' else nombre.startswith('radiograf')


def get_repositorio(db: AsyncSession = Depends(get_db)) -> RepositorioImagenSql:
    return RepositorioImagenSql(db)


def _limite_para(mime: str) -> int:
    limite = settings.imagenes_dicom_max_mb if 'dicom' in mime else settings.imagenes_max_mb
    return limite * 1024 * 1024


@router.get('/ecografia/pacientes')
async def pacientes_ecografia(buscar: str = Query(min_length=2, max_length=100),
                              usuario: Usuario = Depends(usuario_actual),
                              db: AsyncSession = Depends(get_db)):
    _validar_rol(usuario, 'ecografia')
    from app.consultas.infrastructure.persistence.repository import SqlAlchemyConsultaRepository
    from app.consultas.application.use_cases.consultar_pacientes import ConsultarPacientes
    return await ConsultarPacientes(SqlAlchemyConsultaRepository(db)).ejecutar(buscar, 1, 20)


@router.get('/ecografia/catalogo')
async def catalogo_ecografia(usuario: Usuario = Depends(usuario_actual),
                             repositorio: RepositorioImagenSql = Depends(get_repositorio)):
    _validar_rol(usuario, 'ecografia')
    return await repositorio.listar_catalogo_imagen()


@router.post('/ecografia/solicitudes', status_code=201)
async def solicitud_ecografia(datos: SolicitudEcografiaRequest,
                              usuario: Usuario = Depends(usuario_actual),
                              repositorio: RepositorioImagenSql = Depends(get_repositorio)):
    _validar_rol(usuario, 'ecografia')
    from app.imagenes.application.use_cases.solicitar_ecografia import SolicitarEcografia
    try:
        datos.validar_estudios()
        catalogo = await repositorio.listar_catalogo_imagen()
        if not set(datos.tipo_estudio_ids) <= {t['id'] for t in catalogo}:
            raise SolicitudInvalida('Selecciona tipos de ecografía activos.')
        sid = await SolicitarEcografia(repositorio).ejecutar(datos.modelo_solicitud(), usuario.id)
    except (SolicitudInvalida, ValueError) as error:
        raise HTTPException(422, str(error)) from None
    return {'solicitud_id': sid}


@router.get('/bandeja', response_model=list[EstudioPendienteResponse])
async def bandeja(
    modalidad: str = Query(default='ecografia', pattern='^(ecografia|rayos_x)$'),
    usuario: Usuario = Depends(usuario_actual),
    repositorio: RepositorioImagenSql = Depends(get_repositorio),
):
    _validar_rol(usuario, modalidad)
    estudios = await ListarBandeja(repositorio).ejecutar()
    return [e for e in estudios if _nombre_modalidad(e.tipo_estudio_nombre, modalidad)]


@router.get('/estudios/{estudio_id}', response_model=EstudioDetalleResponse)
async def detalle_estudio(
    estudio_id: int,
    modalidad: str = Query(default='ecografia', pattern='^(ecografia|rayos_x)$'),
    usuario: Usuario = Depends(usuario_actual),
    repositorio: RepositorioImagenSql = Depends(get_repositorio),
):
    _validar_rol(usuario, modalidad)
    try:
        estudio = await ObtenerEstudioImagen(repositorio).ejecutar(estudio_id)
    except EstudioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El estudio no existe.') from None
    if not _estudio_de_modalidad(estudio, modalidad):
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El estudio no existe.')
    return EstudioDetalleResponse(
        estudio_id=estudio.estudio_id,
        referencia_estudio=estudio.referencia_estudio,
        referencia_solicitud=estudio.referencia_solicitud,
        paciente_nombre=estudio.paciente_nombre,
        tipo_estudio_nombre=estudio.tipo_estudio_nombre,
        estado=estudio.estado,
        fecha_solicitud=estudio.fecha_solicitud,
        informe=_informe(estudio.informe),
        tipo_estudio_codigo=estudio.tipo_estudio_codigo,
        codigo_paciente=estudio.codigo_paciente,
        historia_clinica=estudio.historia_clinica,
        fecha_nacimiento=estudio.fecha_nacimiento,
        medico_solicitante=estudio.medico_solicitante,
        organos=list(ORGANOS.get(estudio.tipo_estudio_codigo, ())),
        max_archivos=settings.imagenes_max_archivos,
    )


@router.post('/estudios/{estudio_id}/informes', response_model=InformeImagenResponse)
async def guardar_informe(
    estudio_id: int,
    modalidad: str = Query(default='ecografia', pattern='^(ecografia|rayos_x)$'),
    usuario: Usuario = Depends(usuario_actual),
    repositorio: RepositorioImagenSql = Depends(get_repositorio),
    descripcion: str | None = Form(default=None, max_length=8000),
    archivos: list[UploadFile] = File(default=[]),
    datos_ecografia: str | None = Form(default=None, max_length=40000),
    conservar_archivos: str | None = Form(default=None, max_length=4000),
):
    _validar_rol(usuario, modalidad)
    await _comprobar_estudio(estudio_id, modalidad, repositorio)
    try:
        datos = json.loads(datos_ecografia) if datos_ecografia is not None else None
        conservar = json.loads(conservar_archivos) if conservar_archivos is not None else None
        if (datos_ecografia is not None and (not isinstance(datos, dict) or modalidad != 'ecografia')
                or conservar_archivos is not None and not isinstance(conservar, list)):
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(422, 'Los datos del informe o de sus adjuntos no son válidos.') from None
    if len(archivos) > settings.imagenes_max_archivos:
        raise HTTPException(400, f'Como máximo {settings.imagenes_max_archivos} archivos por estudio.')
    caso = GuardarInforme(
        repositorio, AlmacenS3() if settings.imagenes_s3_bucket else AlmacenLocal(), settings.imagenes_tipos_lista,
        settings.imagenes_max_mb * 1024 * 1024, settings.imagenes_max_archivos,
    )
    entradas = []
    for archivo in archivos:
        mime = (archivo.content_type or '').lower()
        entradas.append({'nombre': archivo.filename, 'mime': mime,
                         'contenido': await archivo.read(_limite_para(mime) + 1)})
        await archivo.close()
    try:
        informe, _ = await caso.ejecutar(estudio_id, descripcion, entradas, usuario.id,
                                       datos_ecografia=datos, conservar_archivos=conservar)
    except EstudioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El estudio no existe.') from None
    except FormatoNoAdmitido as error:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(error)) from None
    except (ArchivoVacio, InformeSinContenido) as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None
    except ArchivoDemasiadoGrande as error:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, str(error)) from None
    except InformeYaPublicado as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from None
    except SolicitudInvalida as error:
        raise HTTPException(422, str(error)) from None
    except AlmacenNoDisponible:
        raise HTTPException(503, 'No se pudo guardar el adjunto. Intenta nuevamente.') from None
    return _informe(informe)


@router.post('/estudios/{estudio_id}/informes/publicar', response_model=ResultadoAccionResponse)
async def publicar_informe(
    estudio_id: int,
    modalidad: str = Query(default='ecografia', pattern='^(ecografia|rayos_x)$'),
    usuario: Usuario = Depends(usuario_actual),
    repositorio: RepositorioImagenSql = Depends(get_repositorio),
):
    _validar_rol(usuario, modalidad)
    await _comprobar_estudio(estudio_id, modalidad, repositorio)
    try:
        informe = await PublicarInforme(repositorio).ejecutar(estudio_id, usuario.id)
    except EstudioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El estudio no existe.') from None
    except (InformeSinContenido, InformeYaPublicado) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from None
    except SolicitudInvalida as error:
        raise HTTPException(422, str(error)) from None
    return ResultadoAccionResponse(
        estudio_id=estudio_id, estado='publicado', numero_version=informe.numero_version,
    )


def _informe(informe):
    if informe is None:
        return None
    return InformeImagenResponse(
        id=informe.id, estudio_id=informe.estudio_id, numero_version=informe.numero_version,
        descripcion_texto=informe.descripcion_texto, estado=informe.estado,
        fecha_hora_publicacion=informe.fecha_hora_publicacion,
        archivos=[ArchivoImagenResponse.model_validate(a) for a in informe.archivos],
        datos_ecografia=informe.datos_ecografia,
    )


def _nombre_modalidad(nombre: str, modalidad: str) -> bool:
    texto = nombre.casefold()
    return texto.startswith('ecograf') if modalidad == 'ecografia' else texto.startswith('radiograf')


async def _comprobar_estudio(estudio_id: int, modalidad: str, repositorio: RepositorioImagenSql) -> None:
    try:
        estudio = await ObtenerEstudioImagen(repositorio).ejecutar(estudio_id)
    except EstudioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El estudio no existe.') from None
    if not _estudio_de_modalidad(estudio, modalidad):
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El estudio no existe.')
