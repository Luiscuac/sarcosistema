"""Descarga de archivos clinicos: medico (ve su paciente) y radiologo (su trabajo)."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.config.database import get_db
from app.imagenes.domain.errors import ArchivoNoEncontrado, EstudioNoEncontrado
from app.imagenes.infrastructure.persistence.repository import RepositorioImagenSql
from app.imagenes.infrastructure.storage.almacen_local import AlmacenLocal

router = APIRouter(prefix='/imagenes/archivos', tags=['imagenes'])


def get_repositorio(db: AsyncSession = Depends(get_db)) -> RepositorioImagenSql:
    return RepositorioImagenSql(db)


@router.get('/{archivo_id}')
async def descargar_archivo(
    archivo_id: int,
    usuario: Usuario = Depends(usuario_actual),
    repositorio: RepositorioImagenSql = Depends(get_repositorio),
    almacen: AlmacenLocal = Depends(lambda: AlmacenLocal()),
):
    """Solo el medico (su paciente) o el radiologo (su trabajo) descargan."""
    if usuario.rol not in ('medico', 'imagenes'):
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Sin acceso a este archivo.')

    try:
        archivo = await repositorio.obtener_archivo(archivo_id)
    except ArchivoNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Archivo no encontrado.') from None
    if archivo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Archivo no encontrado.')

    # El radiologo solo baja lo de su bandeja; el medico solo lo publicado de su paciente.
    estudio = await repositorio.obtener_estudio_de_archivo(archivo_id)
    if usuario.rol == 'imagenes' and estudio.estado not in (
        'pendiente_muestra', 'resultado_en_preparacion', 'publicado',
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Sin acceso a este archivo.')
    if usuario.rol == 'medico' and estudio.estado != 'publicado':
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'El estudio no está publicado.')

    try:
        ruta = almacen.ruta_absoluta(archivo.url_archivo)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Archive no disponible.') from None

    return FileResponse(
        ruta, media_type=archivo.mime_type, filename=archivo.nombre_original,
        content_disposition_type='attachment',
    )


__all__ = ['router', 'EstudioNoEncontrado']
