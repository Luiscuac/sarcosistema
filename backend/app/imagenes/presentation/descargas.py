"""Descarga de archivos clinicos: medico (ve su paciente) y radiologo (su trabajo)."""
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.config.database import get_db
from app.config.settings import settings
from app.imagenes.domain.errors import ArchivoNoEncontrado, EstudioNoEncontrado
from app.imagenes.infrastructure.persistence.repository import RepositorioImagenSql
from app.imagenes.infrastructure.storage.almacen_local import AlmacenLocal
from app.imagenes.infrastructure.storage.almacen_s3 import AlmacenNoDisponible, AlmacenS3

# El prefijo /imagenes lo aplica app.imagenes.router (composición única del módulo).
router = APIRouter(tags=['imagenes'])


def get_repositorio(db: AsyncSession = Depends(get_db)) -> RepositorioImagenSql:
    return RepositorioImagenSql(db)


@router.get('/archivos/{archivo_id}')
async def descargar_archivo(
    archivo_id: int,
    usuario: Usuario = Depends(usuario_actual),
    repositorio: RepositorioImagenSql = Depends(get_repositorio),
    almacen: AlmacenLocal = Depends(lambda: AlmacenLocal()),
):
    """Solo el medico (su paciente) o el radiologo (su trabajo) descargan."""
    if usuario.rol not in ('medico', 'imagenes', 'rayos_x'):
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Sin acceso a este archivo.')

    try:
        archivo = await repositorio.obtener_archivo(archivo_id)
    except ArchivoNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Archivo no encontrado.') from None
    if archivo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Archivo no encontrado.')

    # El personal solo baja archivos de su modalidad; el medico ve solo publicados.
    estudio = await repositorio.obtener_estudio_de_archivo(archivo_id)
    modalidad = 'ecografia' if usuario.rol == 'imagenes' else 'rayos_x'
    if usuario.rol in ('imagenes', 'rayos_x') and (
        not (estudio.tipo_estudio_nombre.casefold().startswith('ecograf') if modalidad == 'ecografia'
             else estudio.tipo_estudio_nombre.casefold().startswith('radiograf'))
        or estudio.estado not in (
        'pendiente_muestra', 'resultado_en_preparacion', 'publicado',
        )
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Sin acceso a este archivo.')
    if usuario.rol == 'medico' and estudio.estado != 'publicado':
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'El estudio no está publicado.')

    try:
        if settings.imagenes_s3_bucket:
            contenido = await AlmacenS3().leer(archivo.url_archivo, archivo.tamano_bytes)
            nombre = quote(archivo.nombre_original, safe='')
            return Response(contenido, media_type=archivo.mime_type, headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{nombre}",
                'Cache-Control': 'no-store',
                'X-Content-Type-Options': 'nosniff',
            })
        ruta = almacen.ruta_absoluta(archivo.url_archivo)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Archive no disponible.') from None
    except AlmacenNoDisponible:
        raise HTTPException(503, 'No se pudo recuperar el adjunto. Intenta nuevamente.') from None

    return FileResponse(
        ruta, media_type=archivo.mime_type, filename=archivo.nombre_original,
        content_disposition_type='attachment',
    )


__all__ = ['router', 'EstudioNoEncontrado']
