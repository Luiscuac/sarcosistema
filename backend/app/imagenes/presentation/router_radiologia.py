"""Radiologia convencional: recepcion, adquisicion, imagenes e informe estructurado.

Contrato: docs/imagenes/radiologia-api.md. Roles: `rayos_x` (a cargo de todo el flujo: recepcion, adquisicion, informe y validacion)
y `medico` (solicitante).
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.config.database import get_db
from app.config.settings import settings
from app.imagenes.domain import radiologia as reglas
from app.imagenes.domain.errors import EstudioNoEncontrado
from app.imagenes.application.triaje import nivel_prioridad
from app.imagenes.infrastructure.archivos import limite_archivo, mime_por_firma
from app.imagenes.infrastructure.persistence.repositorio_radiologia import ConflictoRadiologia, RepositorioRadiologiaSql
from app.imagenes.infrastructure.persistence.repositorio_triaje import RepositorioTriajeSql
from app.imagenes.infrastructure.storage.almacen_local import AlmacenLocal

router = APIRouter(prefix='/radiologia', tags=['radiologia'])

TECNICO, MEDICO = 'rayos_x', 'medico'  # TECNICO: personal de Rayos X, a cargo de todo el flujo
MIMES_IMAGEN = ('image/jpeg', 'image/png', 'application/dicom')
EXTENSIONES = {'image/jpeg': 'jpg', 'image/png': 'png', 'application/dicom': 'dcm', 'application/pdf': 'pdf'}


def con_rol(*roles: str):
    async def verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, 'Tu rol no permite esta acción en Rayos X.')
        return usuario
    return verificar


def get_repositorio(db: AsyncSession = Depends(get_db)) -> RepositorioRadiologiaSql:
    return RepositorioRadiologiaSql(db)


def _error(error: Exception) -> HTTPException:
    if isinstance(error, EstudioNoEncontrado):
        return HTTPException(status.HTTP_404_NOT_FOUND, 'El estudio no existe o no pertenece a Rayos X.')
    if isinstance(error, ConflictoRadiologia):
        detalle = {'mensaje': error.mensaje, 'pendientes': error.pendientes} if error.pendientes else error.mensaje
        return HTTPException(status.HTTP_409_CONFLICT, detalle)
    if isinstance(error, reglas.ReglaRadiologia):
        return HTTPException(status.HTTP_400_BAD_REQUEST, str(error))
    raise error


def permisos(rol: str, detalle: dict) -> dict:
    """Acciones disponibles segun rol y estado. La interfaz no recalcula estas reglas."""
    estado = detalle['estudio']['estado']
    etapa = detalle['estudio']['etapa']
    abierto = estado in ('pendiente_muestra', 'resultado_en_preparacion')
    tecnico = rol == TECNICO  # el personal de Rayos X hace todo el flujo, incluido informar y validar
    return {
        'registrar_adquisicion': tecnico and abierto,
        'gestionar_imagenes': tecnico and abierto,
        'redactar_informe': tecnico and estado == 'resultado_en_preparacion',
        'validar': tecnico and estado == 'resultado_en_preparacion',
        'agregar_adenda': tecnico and estado == 'publicado',
        'adjuntar_externo': tecnico and (abierto or estado == 'publicado'),
        'marcar_no_realizado': tecnico and abierto and etapa != 'borrador',
        'entregar': tecnico and etapa == 'validado',
    }


async def _detalle(repositorio: RepositorioRadiologiaSql, estudio_id: int, usuario: Usuario) -> dict:
    detalle = await repositorio.detalle(estudio_id)
    await _con_triaje(repositorio, [detalle['estudio']])
    return detalle | {'permisos': permisos(usuario.rol, detalle)}


async def _con_triaje(repositorio: RepositorioRadiologiaSql, filas: list[dict]) -> list[dict]:
    """Prioridad visual experimental (solo torax); nunca bloquea el listado."""
    torax = [f['estudio_id'] for f in filas if f['tipo_estudio_codigo'] == 'RX_TORAX']
    if not torax:
        return filas
    try:
        resumen = await RepositorioTriajeSql(repositorio.db).triaje_por_estudio(torax)
        if resumen:
            alta, media = _umbrales_triaje()
            for fila in filas:
                r = resumen.get(fila['estudio_id'])
                if r:
                    fila['triaje'] = r | {'nivel': nivel_prioridad(r['indice'], alta, media)}
    except Exception:  # noqa: BLE001 - el triaje es accesorio
        pass
    return filas


def _umbrales_triaje() -> tuple[float, float]:
    from app.imagenes.infrastructure.vision.indice import cargar_indice

    provisional = cargar_indice()['umbrales_provisionales']
    alta = settings.radiology_triage_umbral_alta
    media = settings.radiology_triage_umbral_media
    return (provisional['alta'] if alta is None else alta,
            provisional['media'] if media is None else media)


# ---------- esquemas ----------

class Texto(BaseModel):
    @field_validator('*', mode='before')
    @classmethod
    def recortar(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor


class EstudioSolicitado(Texto):
    tipo_estudio_id: int = Field(gt=0)
    lateralidad: Literal['derecha', 'izquierda', 'bilateral'] | None = None
    protocolo: str | None = Field(default=None, max_length=40)
    proyecciones: list[str] = Field(default_factory=list, max_length=20)
    indicacion: str | None = Field(default=None, max_length=1000)
    observaciones: str | None = Field(default=None, max_length=1000)
    detalle_region: str | None = Field(default=None, max_length=200)


class SolicitudNueva(Texto):
    paciente_id: int = Field(gt=0)
    prioridad: Literal['urgente', 'sin_prioridad'] = 'sin_prioridad'
    procedencia: Literal['este_centro', 'otro_centro'] = 'este_centro'
    medico_solicitante_id: int | None = Field(default=None, gt=0)
    medico_solicitante_nombre: str | None = Field(default=None, max_length=200)
    establecimiento_solicitante_nombre: str | None = Field(default=None, max_length=200)
    diagnostico_principal: str | None = Field(default=None, max_length=500)
    clave_idempotencia: UUID
    estudios: list[EstudioSolicitado] = Field(min_length=1, max_length=15)


class AdquisicionDatos(Texto):
    proyecciones_realizadas: list[str] = Field(default_factory=list, max_length=20)
    lateralidad_realizada: str | None = None
    posicion_paciente: str | None = None
    fecha_hora_adquisicion: datetime | None = None
    operador_nombre: str | None = Field(default=None, max_length=200)
    calidad: str | None = None
    limitaciones: str | None = Field(default=None, max_length=1000)
    repeticiones: int = Field(default=0, ge=0, le=20)
    motivo_repeticion: str | None = Field(default=None, max_length=500)
    parametros: dict = Field(default_factory=dict)
    observaciones: str | None = Field(default=None, max_length=1000)


class Motivo(Texto):
    motivo: str = Field(min_length=3, max_length=500)


class ProyeccionImagen(BaseModel):
    proyeccion_codigo: str | None = Field(default=None, max_length=40)


class ContenidoInforme(BaseModel):
    contenido: dict


class BorradorInforme(ContenidoInforme):
    texto_final: str | None = Field(default=None, max_length=reglas.MAX_TEXTO_FINAL)
    version_edicion: int | None = None


class Validacion(Texto):
    version_edicion: int
    responsable_nombre: str = Field(min_length=3, max_length=200)
    registro_profesional: str | None = Field(default=None, max_length=80)
    confirmo: Literal[True]


class AdendaNueva(Texto):
    motivo: str = Field(min_length=3, max_length=500)
    texto: str = Field(min_length=3, max_length=4000)
    autor_nombre: str = Field(min_length=3, max_length=200)
    registro_profesional: str | None = Field(default=None, max_length=80)


class Entrega(Texto):
    entregado_a: str = Field(min_length=2, max_length=200)


class CambioCatalogo(BaseModel):
    activo: bool


# ---------- catalogo, pacientes y medicos ----------

@router.get('/catalogo')
async def catalogo(todos: bool = False, usuario: Usuario = Depends(con_rol(TECNICO, MEDICO)),
                   repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await repositorio.catalogo(incluir_inactivos=todos and usuario.rol == TECNICO)


@router.patch('/catalogo/estudios/{tipo_estudio_id}')
async def cambiar_catalogo(tipo_estudio_id: int, datos: CambioCatalogo, usuario: Usuario = Depends(con_rol(TECNICO)),
                           repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    estudio = await repositorio.cambiar_activo(tipo_estudio_id, datos.activo, usuario.id)
    if estudio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El estudio no pertenece al catálogo de Rayos X.')
    return estudio


def _laboratorio(db: AsyncSession):
    # Pacientes y medicos son compartidos: se reutilizan los casos de uso de Laboratorio.
    from app.laboratorio.presentation.routes.router import get_service
    return get_service(db)


@router.get('/pacientes')
async def buscar_pacientes(termino: str = Query(min_length=2, max_length=100), db: AsyncSession = Depends(get_db),
                           _: Usuario = Depends(con_rol(TECNICO))):
    from app.laboratorio.presentation.schemas import PacienteResponse
    return [PacienteResponse.model_validate(p) for p in await _laboratorio(db).buscar_pacientes(termino)]


@router.post('/pacientes', status_code=status.HTTP_201_CREATED)
async def crear_paciente(datos: dict, db: AsyncSession = Depends(get_db), usuario: Usuario = Depends(con_rol(TECNICO))):
    from pydantic import ValidationError
    from app.laboratorio.domain.entities import PacienteNuevo
    from app.laboratorio.presentation.schemas import CrearPacienteRequest, PacienteResponse
    try:
        solicitud = CrearPacienteRequest.model_validate(datos)
    except ValidationError as error:
        mensaje = error.errors()[0].get('msg', 'Datos del paciente no válidos').removeprefix('Value error, ')
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, mensaje) from None
    try:
        paciente = await _laboratorio(db).crear_paciente(PacienteNuevo(**solicitud.model_dump()), usuario.id)
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, 'Ya existe un paciente con ese tipo y número de documento.') from None
    return PacienteResponse.model_validate(paciente)


@router.get('/medicos')
async def buscar_medicos(termino: str = Query(min_length=2, max_length=100), db: AsyncSession = Depends(get_db),
                         _: Usuario = Depends(con_rol(TECNICO))):
    return await _laboratorio(db).listar_medicos(termino)


# ---------- solicitudes y listados ----------

@router.post('/solicitudes', status_code=status.HTTP_201_CREATED)
async def crear_solicitud(datos: SolicitudNueva, usuario: Usuario = Depends(con_rol(TECNICO, MEDICO)),
                          repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    cuerpo = datos.model_dump() | {'clave_idempotencia': str(datos.clave_idempotencia)}
    try:
        return await repositorio.crear_solicitud(cuerpo, usuario.id, usuario.rol)
    except (reglas.ReglaRadiologia, ConflictoRadiologia) as error:
        raise _error(error) from None
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, 'La solicitud se recibió duplicada. Actualiza la lista antes de reintentar.') from None


@router.get('/estudios')
async def listar_estudios(vista: Literal['activos', 'finalizados'] = 'activos', _: Usuario = Depends(con_rol(TECNICO)),
                          repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _con_triaje(repositorio, await repositorio.listar_estudios(vista))


@router.get('/solicitudes/{solicitud_id}')
async def obtener_solicitud(solicitud_id: int, _: Usuario = Depends(con_rol(TECNICO)),
                            repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    solicitud = await repositorio.solicitud(solicitud_id)
    if solicitud is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'La solicitud no existe o no es de Rayos X.')
    paciente = await repositorio.paciente(solicitud.pop('paciente_id'))
    estudios = await _con_triaje(repositorio, await repositorio.listar_estudios(solicitud_id=solicitud_id))
    return {'solicitud': solicitud, 'paciente': paciente, 'estudios': estudios}


@router.get('/pacientes/{paciente_id}/estudios')
async def estudios_del_paciente(paciente_id: int, _: Usuario = Depends(con_rol(TECNICO)),
                                repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    paciente = await repositorio.paciente(paciente_id)
    if paciente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El paciente no existe.')
    return {'paciente': paciente, 'estudios': await repositorio.listar_estudios(paciente_id=paciente_id)}


@router.get('/estudios/{estudio_id}')
async def obtener_estudio(estudio_id: int, usuario: Usuario = Depends(con_rol(TECNICO, MEDICO)),
                          repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    try:
        detalle = await _detalle(repositorio, estudio_id, usuario)
    except EstudioNoEncontrado as error:
        raise _error(error) from None
    # El medico consulta solo informes validados, igual que en el historial del paciente.
    if usuario.rol == MEDICO and detalle['estudio']['estado'] != 'publicado':
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'El informe de este estudio todavía no está validado.')
    return detalle


async def _operar(operacion, repositorio: RepositorioRadiologiaSql, estudio_id: int, usuario: Usuario) -> dict:
    try:
        await operacion
        return await _detalle(repositorio, estudio_id, usuario)
    except (EstudioNoEncontrado, ConflictoRadiologia, reglas.ReglaRadiologia) as error:
        raise _error(error) from None


# ---------- adquisicion e imagenes ----------

@router.put('/estudios/{estudio_id}/adquisicion')
async def guardar_adquisicion(estudio_id: int, datos: AdquisicionDatos, usuario: Usuario = Depends(con_rol(TECNICO)),
                              repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.guardar_adquisicion(estudio_id, datos.model_dump(), usuario.id), repositorio, estudio_id, usuario)


@router.post('/estudios/{estudio_id}/adquisicion/completar')
async def completar_adquisicion(estudio_id: int, usuario: Usuario = Depends(con_rol(TECNICO)),
                                repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.completar_adquisicion(estudio_id, usuario.id), repositorio, estudio_id, usuario)


async def _leer_radiografia(archivo: UploadFile) -> dict:
    """Valida por contenido real (firma), no por la extension ni el tipo declarado."""
    nombre = (archivo.filename or 'imagen')[:200]
    contenido = await archivo.read(limite_archivo('application/dicom') + 1)
    await archivo.close()
    if not contenido:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f'{nombre}: el archivo llegó vacío.')
    mime = mime_por_firma('', contenido)
    if mime not in MIMES_IMAGEN:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f'{nombre}: solo se admiten imágenes JPG, PNG o DICOM.')
    if len(contenido) > limite_archivo(mime):
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f'{nombre}: supera el tamaño máximo permitido.')
    return {'nombre_original': nombre, 'mime_type': mime, 'tamano_bytes': len(contenido),
            'hash_sha256': hashlib.sha256(contenido).hexdigest(), 'contenido': contenido}


@router.post('/estudios/{estudio_id}/imagenes')
async def subir_imagenes(estudio_id: int, archivos: list[UploadFile] = File(...), proyecciones: list[str] = Form(default=[]),
                         usuario: Usuario = Depends(con_rol(TECNICO)),
                         repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    if not 1 <= len(archivos) <= settings.imagenes_max_archivos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f'Adjunta entre 1 y {settings.imagenes_max_archivos} imágenes por envío.')
    try:
        await repositorio.base(estudio_id)
    except EstudioNoEncontrado as error:
        raise _error(error) from None
    almacen, metadatos = AlmacenLocal(), []
    for indice, archivo in enumerate(archivos):
        leido = await _leer_radiografia(archivo)
        contenido = leido.pop('contenido')
        leido['url_archivo'] = await almacen.guardar(contenido, estudio_id, leido['hash_sha256'], EXTENSIONES[leido['mime_type']])
        leido['proyeccion_codigo'] = (proyecciones[indice] if indice < len(proyecciones) else '') or None
        metadatos.append(leido)

    async def operacion():
        creadas = await repositorio.agregar_imagenes(estudio_id, metadatos, usuario.id)
        base = await repositorio.base(estudio_id)
        if settings.radiology_ai_enabled and base['fila']['tipo_estudio_codigo'] == 'RX_TORAX':
            # Triaje visual experimental: solo torax; no bloquea la carga ni modifica el informe.
            from types import SimpleNamespace
            await RepositorioTriajeSql(repositorio.db).encolar_triaje(
                estudio_id, [SimpleNamespace(**c) for c in creadas],
            )

    return await _operar(operacion(), repositorio, estudio_id, usuario)


@router.patch('/estudios/{estudio_id}/imagenes/{imagen_id}')
async def asignar_proyeccion(estudio_id: int, imagen_id: int, datos: ProyeccionImagen, usuario: Usuario = Depends(con_rol(TECNICO)),
                             repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.asignar_proyeccion(estudio_id, imagen_id, datos.proyeccion_codigo or None, usuario.id),
                         repositorio, estudio_id, usuario)


@router.post('/estudios/{estudio_id}/imagenes/{imagen_id}/retirar')
async def retirar_imagen(estudio_id: int, imagen_id: int, datos: Motivo, usuario: Usuario = Depends(con_rol(TECNICO)),
                         repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.retirar_imagen(estudio_id, imagen_id, datos.motivo, usuario.id), repositorio, estudio_id, usuario)


@router.post('/estudios/{estudio_id}/no-realizado')
async def no_realizado(estudio_id: int, datos: Motivo, usuario: Usuario = Depends(con_rol(TECNICO)),
                       repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.marcar_no_realizado(estudio_id, datos.motivo, usuario.id), repositorio, estudio_id, usuario)


# ---------- informe ----------

@router.post('/estudios/{estudio_id}/informe/vista-previa')
async def vista_previa(estudio_id: int, datos: ContenidoInforme, _: Usuario = Depends(con_rol(TECNICO)),
                       repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    try:
        config = (await repositorio.base(estudio_id))['config']
        return {'texto': reglas.componer_informe(config, reglas.normalizar_contenido(config, datos.contenido))}
    except (EstudioNoEncontrado, reglas.ReglaRadiologia) as error:
        raise _error(error) from None


@router.put('/estudios/{estudio_id}/informe/borrador')
async def guardar_borrador(estudio_id: int, datos: BorradorInforme, usuario: Usuario = Depends(con_rol(TECNICO)),
                           repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.guardar_borrador(estudio_id, datos.contenido, datos.texto_final, datos.version_edicion, usuario.id),
                         repositorio, estudio_id, usuario)


@router.post('/estudios/{estudio_id}/informe/validar')
async def validar_informe(estudio_id: int, datos: Validacion, usuario: Usuario = Depends(con_rol(TECNICO)),
                          repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.validar(estudio_id, datos.version_edicion, datos.responsable_nombre,
                                             datos.registro_profesional or None, usuario.id), repositorio, estudio_id, usuario)


@router.post('/estudios/{estudio_id}/adendas')
async def agregar_adenda(estudio_id: int, datos: AdendaNueva, usuario: Usuario = Depends(con_rol(TECNICO)),
                         repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.agregar_adenda(estudio_id, datos.motivo, datos.texto, datos.autor_nombre,
                                                    datos.registro_profesional or None, usuario.id), repositorio, estudio_id, usuario)


@router.post('/estudios/{estudio_id}/entregar')
async def entregar(estudio_id: int, datos: Entrega, usuario: Usuario = Depends(con_rol(TECNICO)),
                   repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.entregar(estudio_id, datos.entregado_a, usuario.id), repositorio, estudio_id, usuario)


# ---------- informes externos ----------

@router.post('/estudios/{estudio_id}/informes-externos')
async def adjuntar_externo(estudio_id: int, archivo: UploadFile = File(...), establecimiento: str = Form(min_length=2, max_length=200),
                           profesional: str | None = Form(default=None, max_length=200), fecha_informe: date | None = Form(default=None),
                           observaciones: str | None = Form(default=None, max_length=1000),
                           usuario: Usuario = Depends(con_rol(TECNICO)),
                           repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    try:
        await repositorio.base(estudio_id)
    except EstudioNoEncontrado as error:
        raise _error(error) from None
    limite = settings.imagenes_max_mb * 1024 * 1024
    contenido = await archivo.read(limite + 1)
    await archivo.close()
    if not contenido.startswith(b'%PDF-'):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, 'El informe externo debe ser un archivo PDF.')
    if len(contenido) > limite:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, 'El PDF supera el tamaño máximo permitido.')
    if fecha_informe and fecha_informe > date.today():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'La fecha del informe externo no puede ser futura.')
    sha = hashlib.sha256(contenido).hexdigest()
    url = await AlmacenLocal().guardar(contenido, estudio_id, f'externo-{sha}', 'pdf')
    metadatos = {'nombre_original': (archivo.filename or 'informe-externo.pdf')[:200], 'url_archivo': url,
                 'mime_type': 'application/pdf', 'tamano_bytes': len(contenido), 'hash_sha256': sha}
    campos = {'establecimiento': establecimiento.strip(), 'profesional': (profesional or '').strip() or None,
              'fecha_informe': fecha_informe, 'observaciones': (observaciones or '').strip() or None}
    return await _operar(repositorio.agregar_externo(estudio_id, metadatos, campos, usuario.id), repositorio, estudio_id, usuario)


@router.post('/estudios/{estudio_id}/informes-externos/{externo_id}/retirar')
async def retirar_externo(estudio_id: int, externo_id: int, datos: Motivo, usuario: Usuario = Depends(con_rol(TECNICO)),
                          repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    return await _operar(repositorio.retirar_externo(estudio_id, externo_id, datos.motivo, usuario.id), repositorio, estudio_id, usuario)


@router.get('/informes-externos/{externo_id}/archivo')
async def descargar_externo(externo_id: int, usuario: Usuario = Depends(con_rol(TECNICO, MEDICO)),
                            repositorio: RepositorioRadiologiaSql = Depends(get_repositorio)):
    externo = await repositorio.externo(externo_id)
    if externo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El informe externo no está disponible.')
    if usuario.rol == MEDICO and externo['estado'] != 'publicado':
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'El estudio todavía no está validado.')
    try:
        ruta = AlmacenLocal().ruta_absoluta(externo['url_archivo'])
    except (FileNotFoundError, ValueError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'El archivo no está disponible.') from None
    return FileResponse(ruta, media_type='application/pdf', filename=externo['nombre_original'],
                        content_disposition_type='inline', headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})
