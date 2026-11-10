"""Endpoints de asistencia radiológica local (RAG) para el médico.

Namespace propio bajo /imagenes/analisis para no chocar con las rutas clínicas
de ecografía del radiólogo (bandeja, subida y publicación).
"""
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.accesos.presentation.dependencies.role_required import requiere_rol
from app.config.database import get_db
from app.config.settings import settings
from app.imagenes.infrastructure.archivos import leer_archivo_local
from app.imagenes.infrastructure.persistence.repository import EstudiosRepository
from app.imagenes.presentation.schemas import AnalisisNuevo, RevisionNueva

BASE = Path(__file__).resolve().parents[3]
router = APIRouter(prefix='/analisis', tags=['imagenes-analisis'],
                   dependencies=[Depends(requiere_rol('medico'))])


def get_repository(db=Depends(get_db)):
    return EstudiosRepository(db)


def raiz_archivos():
    ruta = Path(settings.radiology_storage_dir)
    return ruta if ruta.is_absolute() else BASE / ruta


def analisis_publico(a):
    return {k: a[k] for k in ('id', 'estudio_id', 'informe_id', 'archivo_id',
                              'archivo_sha256', 'informe_sha256', 'informe_texto',
                              'estado', 'proyeccion', 'resultado',
                              'error_codigo', 'version_revision', 'creado_en',
                              'actualizado_en', 'revisiones') if k in a}


@router.get('/estudios')
async def listar(pagina: int = Query(default=1, ge=1), usuario: Usuario = Depends(usuario_actual),
                 repo=Depends(get_repository)):
    return {'estudios': await repo.listar(usuario.id, pagina),
            'ia_habilitada': settings.radiology_ai_enabled}


@router.get('/estudios/{estudio_id}')
async def detalle(estudio_id: int, usuario: Usuario = Depends(usuario_actual),
                  repo=Depends(get_repository)):
    dato = await repo.obtener(estudio_id, usuario.id)
    if dato is None:
        raise HTTPException(404, 'Estudio no encontrado.')
    if dato['archivo']:
        dato['archivo'] = {k: v for k, v in dato['archivo'].items() if k != 'url_archivo'}
    return dato


@router.get('/estudios/{estudio_id}/archivos/{archivo_id}')
async def archivo(estudio_id: int, archivo_id: int, usuario: Usuario = Depends(usuario_actual),
                  repo=Depends(get_repository)):
    dato = await repo.obtener(estudio_id, usuario.id)
    if not dato or not dato['archivo'] or dato['archivo']['id'] != archivo_id:
        raise HTTPException(404, 'Archivo no encontrado.')
    try:
        contenido, mime = leer_archivo_local(raiz_archivos(), dato['archivo'])
    except ValueError:
        raise HTTPException(409, 'El archivo local no está disponible o no supera la comprobación de integridad.') from None
    return Response(contenido, media_type=mime,
                    headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


@router.post('/estudios/{estudio_id}/analisis', status_code=202)
async def solicitar(estudio_id: int, datos: AnalisisNuevo, usuario: Usuario = Depends(usuario_actual),
                    repo=Depends(get_repository)):
    snapshot = await repo.obtener(estudio_id, usuario.id)
    if snapshot is None:
        raise HTTPException(404, 'Estudio no encontrado.')
    if not settings.radiology_ai_enabled:
        raise HTTPException(503, 'La asistencia radiológica local no está habilitada.')
    try:
        return analisis_publico(await repo.crear_analisis(snapshot, usuario.id, datos.clave, datos.proyeccion))
    except ValueError:
        raise HTTPException(409, 'Solicitud incompatible: revisa archivo, informe o análisis activo y no reutilices una clave con otros datos.') from None


@router.get('/{analisis_id}')
async def obtener_analisis(analisis_id: UUID, usuario: Usuario = Depends(usuario_actual),
                           repo=Depends(get_repository)):
    dato = await repo.obtener_analisis(analisis_id, usuario.id)
    if dato is None:
        raise HTTPException(404, 'Análisis no encontrado.')
    return analisis_publico(dato)


@router.get('/{analisis_id}/fuentes')
async def fuentes(analisis_id: UUID, usuario: Usuario = Depends(usuario_actual),
                  repo=Depends(get_repository)):
    dato = await repo.obtener_analisis(analisis_id, usuario.id)
    if dato is None:
        raise HTTPException(404, 'Análisis no encontrado.')
    return {'fuentes': (dato.get('resultado') or {}).get('rag', {}).get('evidencia', [])}


@router.post('/{analisis_id}/revision')
async def revisar(analisis_id: UUID, datos: RevisionNueva, usuario: Usuario = Depends(usuario_actual),
                  repo=Depends(get_repository)):
    try:
        return analisis_publico(await repo.registrar_revision(
            analisis_id, usuario.id, datos.version, datos.decision, datos.motivo, datos.correccion))
    except LookupError:
        raise HTTPException(404, 'Análisis no encontrado.') from None
    except ValueError:
        raise HTTPException(409, 'La revisión cambió o el análisis no está listo; recarga antes de guardar.') from None
