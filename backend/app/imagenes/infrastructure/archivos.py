import hashlib
from pathlib import Path, PureWindowsPath

from app.imagenes.domain.vision import MAX_IMAGE_BYTES


def leer_archivo_local(raiz: Path, archivo: dict) -> tuple[bytes, str]:
    ruta = archivo['url_archivo']
    relativa = Path(ruta)
    if (not archivo['activo'] or relativa.is_absolute() or PureWindowsPath(ruta).drive
            or ':' in ruta or '..' in ruta.replace('\\', '/').split('/')
            or archivo['mime_type'] not in ('image/png', 'image/jpeg')
            or not 0 < archivo['tamano_bytes'] <= MAX_IMAGE_BYTES):
        raise ValueError('Archivo local no disponible o incompatible.')
    base = raiz.resolve()
    destino = (base / relativa).resolve()
    if not destino.is_relative_to(base):
        raise ValueError('Archivo fuera de la raíz permitida.')
    try:
        with destino.open('rb') as stream:
            datos = stream.read(MAX_IMAGE_BYTES + 1)
    except OSError:
        raise ValueError('Archivo local no disponible.') from None
    if (len(datos) != archivo['tamano_bytes'] or len(datos) > MAX_IMAGE_BYTES
            or hashlib.sha256(datos).hexdigest() != archivo['hash_sha256']):
        raise ValueError('Archivo local con integridad incompatible.')
    mime = 'image/png' if datos.startswith(b'\x89PNG\r\n\x1a\n') else (
        'image/jpeg' if datos.startswith(b'\xff\xd8\xff') else None)
    if mime != archivo['mime_type']:
        raise ValueError('Formato de imagen incompatible.')
    return datos, mime
