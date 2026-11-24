import hashlib
from pathlib import Path, PureWindowsPath

from app.imagenes.domain.vision import MAX_IMAGE_BYTES

MIMES_RADIOGRAFIA = {'png': 'image/png', 'jpeg': 'image/jpeg', 'dicom': 'application/dicom'}
BASE = Path(__file__).resolve().parents[3]


def mime_por_firma(mime_declarado: str, contenido: bytes) -> str:
    """Reconoce PNG, JPEG o DICOM por contenido cuando el tipo declarado lo permite."""
    from app.imagenes.infrastructure.vision.preprocesamiento import detectar_formato

    detectado = MIMES_RADIOGRAFIA.get(detectar_formato(contenido))
    if detectado and (mime_declarado in MIMES_RADIOGRAFIA.values()
                      or mime_declarado in ('', 'application/octet-stream')):
        return detectado
    return mime_declarado


def limite_archivo(mime: str) -> int:
    """Devuelve el límite configurado para DICOM o para imágenes convencionales."""
    from app.config.settings import settings

    limite_mb = settings.imagenes_dicom_max_mb if 'dicom' in mime else settings.imagenes_max_mb
    return limite_mb * 1024 * 1024


def raices_archivos() -> list[Path]:
    """Raíces de lectura: subidas del rol Rayos X (IMAGENES_STORAGE_DIR) y demo (RADIOLOGY_STORAGE_DIR)."""
    from app.config.settings import settings
    raices = []
    for ruta in (settings.imagenes_storage_dir, settings.radiology_storage_dir):
        raiz = Path(ruta) if Path(ruta).is_absolute() else BASE / ruta
        if raiz not in raices:
            raices.append(raiz)
    return raices


def leer_archivo_local(raiz: Path | list[Path], archivo: dict) -> tuple[bytes, str]:
    if isinstance(raiz, (list, tuple)):
        candidatas = [r for r in raiz if (r / archivo['url_archivo']).is_file()] if isinstance(archivo.get('url_archivo'), str) else []
        raiz = candidatas[0] if candidatas else raiz[0]
    ruta = archivo['url_archivo']
    relativa = Path(ruta)
    if (not archivo['activo'] or relativa.is_absolute() or PureWindowsPath(ruta).drive
            or ':' in ruta or '..' in ruta.replace('\\', '/').split('/')
            or archivo['mime_type'] not in MIMES_RADIOGRAFIA.values()
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
    from app.imagenes.infrastructure.vision.preprocesamiento import detectar_formato
    mime = MIMES_RADIOGRAFIA.get(detectar_formato(datos))
    if mime != archivo['mime_type']:
        raise ValueError('Formato de imagen incompatible.')
    return datos, mime
