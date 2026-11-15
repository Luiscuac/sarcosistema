"""Decodificación robusta de radiografías (PNG/JPEG/DICOM) y preprocesamiento XRV.

Acepta lo que entregan equipos y exportadores reales: PNG en paleta, gris de 16 bits, RGBA,
imágenes de alta resolución (se reducen antes de pasar a memoria flotante) y DICOM sin
comprimir o RLE con Modality/VOI LUT. Torch solo se importa en `preparar_imagen`.
"""
import hashlib
from io import BytesIO
import warnings

from app.imagenes.domain.vision import (
    ImagenNoValida, ErrorVision, MAX_IMAGE_BYTES, MAX_RASTER_BYTES, PREPROCESS_VERSION,
)

DECODIFICACION_VERSION = 'decodificacion-v2-png-jpeg-dicom-reduccion2048'
LADO_TRABAJO = 2048
MAX_PIXELES = 60_000_000
MAX_LADO = 16384
MODOS_PNG = ('1', 'L', 'LA', 'P', 'RGB', 'RGBA', 'I', 'I;16', 'I;16B', 'I;16L')
SINTAXIS_SIN_COMPRESION = {
    '1.2.840.10008.1.2', '1.2.840.10008.1.2.1', '1.2.840.10008.1.2.1.99', '1.2.840.10008.1.2.2',
    '1.2.840.10008.1.2.5',  # RLE Lossless: decodificador nativo de pydicom
}
# Comprimidas habituales en equipos de RX; requieren pylibjpeg (+ libjpeg / openjpeg), todo local.
SINTAXIS_COMPRIMIDAS = {
    '1.2.840.10008.1.2.4.50': 'libjpeg', '1.2.840.10008.1.2.4.51': 'libjpeg',   # JPEG Baseline / Extended
    '1.2.840.10008.1.2.4.57': 'libjpeg', '1.2.840.10008.1.2.4.70': 'libjpeg',   # JPEG Lossless
    '1.2.840.10008.1.2.4.90': 'openjpeg', '1.2.840.10008.1.2.4.91': 'openjpeg',  # JPEG 2000
}


def _decodificador_disponible(sintaxis: str) -> bool:
    from importlib.util import find_spec
    modulo = SINTAXIS_COMPRIMIDAS.get(sintaxis)
    return bool(modulo) and find_spec('pylibjpeg') is not None and find_spec(modulo) is not None


def detectar_formato(contenido: bytes) -> str | None:
    if contenido.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if contenido.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    if len(contenido) > 132 and contenido[128:132] == b'DICM':
        return 'dicom'
    return None


def _maxval_por_profundidad(maximo: float) -> int:
    for bits in (8, 10, 12, 14, 16):
        if maximo <= 2 ** bits - 1:
            return 2 ** bits - 1
    return 65535


def _reducir_arreglo(arreglo, lado: int):
    """Reduce un arreglo 2D float con promediado por área (sin aliasing)."""
    from PIL import Image
    import numpy as np
    alto, ancho = arreglo.shape
    escala = lado / max(alto, ancho)
    if escala >= 1:
        return arreglo, False
    nuevo = (max(1, round(ancho * escala)), max(1, round(alto * escala)))
    return np.asarray(Image.fromarray(arreglo.astype(np.float32)).resize(nuevo, Image.Resampling.BOX)), True


def _decodificar_raster(contenido: bytes, formato: str):
    from PIL import Image, UnidentifiedImageError
    import numpy as np
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(contenido)) as imagen:
                if imagen.format not in ('PNG', 'JPEG') or getattr(imagen, 'n_frames', 1) != 1:
                    raise ImagenNoValida('Solo PNG/JPEG de un cuadro, sin animación.')
                if formato == 'png' and imagen.mode not in MODOS_PNG:
                    raise ImagenNoValida('Modo de color PNG no admitido para radiografía.')
                if formato == 'jpeg' and imagen.mode not in ('L', 'RGB', 'CMYK'):
                    raise ImagenNoValida('Modo de color JPEG no admitido para radiografía.')
                ancho, alto = imagen.size
                if min(ancho, alto) < 32 or max(ancho, alto) > MAX_LADO or ancho * alto > MAX_PIXELES:
                    raise ImagenNoValida('Dimensiones no admitidas: máximo 60 megapíxeles y 16384 píxeles por lado.')
                modo = imagen.mode
                imagen.verify()
            with Image.open(BytesIO(contenido)) as imagen:
                if formato == 'jpeg':
                    # Decodificación JPEG reducida y en gris desde el códec (menos memoria).
                    imagen.draft('L', (LADO_TRABAJO, LADO_TRABAJO))
                imagen.load()
                if imagen.mode in ('P', 'LA', 'RGBA', '1', 'CMYK'):
                    # Paleta/alfa: los índices no son niveles de gris; convertir explícitamente.
                    imagen = imagen.convert('L')
                if imagen.mode in ('I;16', 'I;16B', 'I;16L'):
                    imagen = imagen.convert('I')
                if imagen.mode == 'RGB':
                    arreglo = np.asarray(imagen, dtype=np.float32).mean(axis=2)
                    maxval = 255
                elif imagen.mode == 'L':
                    arreglo = np.asarray(imagen, dtype=np.float32)
                    maxval = 255
                else:  # 'I': gris de 16 bits; se escala por la profundidad efectiva.
                    arreglo = np.asarray(imagen, dtype=np.float32)
                    maxval = _maxval_por_profundidad(float(arreglo.max()))
    except ImagenNoValida:
        raise
    except (OSError, ValueError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImagenNoValida('El archivo no es una imagen admitida o está dañado.') from None
    return arreglo, maxval, {'format': formato.upper(), 'original_size': [ancho, alto], 'original_mode': modo,
                             'bits': 8 if maxval == 255 else int(maxval).bit_length()}


def _texto_dicom(ds, atributo):
    valor = getattr(ds, atributo, None)
    return str(valor).strip().upper() or None if valor is not None else None


def _decodificar_dicom(contenido: bytes):
    try:
        import numpy as np
        import pydicom
        from pydicom.pixels import apply_modality_lut, apply_voi_lut
    except ImportError:
        raise ErrorVision('Falta pydicom (dependencia opcional de radiología) para leer DICOM.') from None
    try:
        ds = pydicom.dcmread(BytesIO(contenido), force=False)
    except Exception:
        raise ImagenNoValida('El archivo DICOM está dañado o no es legible.') from None
    sintaxis = str(getattr(getattr(ds, 'file_meta', None), 'TransferSyntaxUID', ''))
    if sintaxis not in SINTAXIS_SIN_COMPRESION and not _decodificador_disponible(sintaxis):
        if sintaxis in SINTAXIS_COMPRIMIDAS:
            raise ImagenNoValida('DICOM comprimido sin decodificador local instalado (pylibjpeg); exporta sin compresión o instala las dependencias de radiología.')
        raise ImagenNoValida('Compresión DICOM no admitida (por ejemplo JPEG-LS); exporta el estudio sin compresión o en JPEG/JPEG 2000.')
    if 'PixelData' not in ds:
        raise ImagenNoValida('El DICOM no contiene imagen.')
    filas, columnas = int(getattr(ds, 'Rows', 0)), int(getattr(ds, 'Columns', 0))
    if int(getattr(ds, 'NumberOfFrames', 1) or 1) != 1:
        raise ImagenNoValida('Solo DICOM de un cuadro (radiografía simple).')
    if min(filas, columnas) < 32 or max(filas, columnas) > MAX_LADO or filas * columnas > MAX_PIXELES:
        raise ImagenNoValida('Dimensiones no admitidas: máximo 60 megapíxeles y 16384 píxeles por lado.')
    fotometria = _texto_dicom(ds, 'PhotometricInterpretation')
    if fotometria not in ('MONOCHROME1', 'MONOCHROME2', 'RGB'):
        raise ImagenNoValida('Interpretación fotométrica DICOM no admitida.')
    try:
        pixeles = ds.pixel_array
        arreglo = apply_modality_lut(pixeles, ds) if fotometria != 'RGB' else pixeles
        if fotometria != 'RGB':
            arreglo = apply_voi_lut(arreglo, ds)
    except Exception:
        raise ImagenNoValida('No se pudieron decodificar los píxeles DICOM.') from None
    arreglo = np.asarray(arreglo, dtype=np.float32)
    if arreglo.ndim == 3:
        arreglo = arreglo.mean(axis=2)
    if not np.isfinite(arreglo).all():
        raise ImagenNoValida('Píxeles DICOM no finitos.')
    minimo, maximo = float(arreglo.min()), float(arreglo.max())
    if maximo <= minimo:
        raise ImagenNoValida('La imagen DICOM no tiene contraste (valor constante).')
    arreglo = (arreglo - minimo) / (maximo - minimo) * 255.0
    if fotometria == 'MONOCHROME1':
        arreglo = 255.0 - arreglo  # en MONOCHROME1 el valor alto es negro
    meta = {'format': 'DICOM', 'original_size': [columnas, filas], 'original_mode': fotometria,
            'bits': int(getattr(ds, 'BitsStored', 0) or 0),
            'dicom': {'modality': _texto_dicom(ds, 'Modality'), 'view_position': _texto_dicom(ds, 'ViewPosition'),
                      'body_part': _texto_dicom(ds, 'BodyPartExamined'), 'photometric': fotometria,
                      'transfer_syntax': sintaxis}}
    return arreglo, 255, meta


def decodificar_radiografia(contenido: bytes):
    """bytes -> (arreglo float32 2D en [0, maxval], maxval, metadatos). Sin torch."""
    if not contenido or len(contenido) > MAX_IMAGE_BYTES:
        raise ImagenNoValida('Imagen vacía o superior al tamaño máximo admitido.')
    formato = detectar_formato(contenido)
    if formato is None:
        raise ImagenNoValida('Firma de archivo no compatible con PNG, JPEG o DICOM.')
    if formato != 'dicom' and len(contenido) > MAX_RASTER_BYTES:
        raise ImagenNoValida('Imagen PNG/JPEG superior al tamaño máximo admitido.')
    if formato == 'dicom':
        arreglo, maxval, meta = _decodificar_dicom(contenido)
    else:
        try:
            import PIL  # noqa: F401
        except ImportError:
            raise ErrorVision('Faltan las dependencias opcionales de radiología.') from None
        arreglo, maxval, meta = _decodificar_raster(contenido, formato)
    arreglo, reducida = _reducir_arreglo(arreglo, LADO_TRABAJO)
    meta |= {'original_sha256': hashlib.sha256(contenido).hexdigest(), 'reducida_a_trabajo': reducida,
             'working_size': [int(arreglo.shape[1]), int(arreglo.shape[0])], 'decodificacion': DECODIFICACION_VERSION}
    return arreglo, maxval, meta


def vista_previa_png(contenido: bytes, lado: int = LADO_TRABAJO) -> bytes:
    """PNG 8 bits en gris para el visor web, válido para cualquier formato admitido."""
    from PIL import Image
    import numpy as np
    arreglo, maxval, _ = decodificar_radiografia(contenido)
    arreglo, _ = _reducir_arreglo(arreglo, lado)
    gris = np.clip(arreglo / maxval * 255.0, 0, 255).round().astype(np.uint8)
    salida = BytesIO()
    Image.fromarray(gris).save(salida, format='PNG', optimize=False)
    return salida.getvalue()


def preparar_imagen(contenido: bytes):
    arreglo, maxval, meta = decodificar_radiografia(contenido)
    try:
        import torch
        import torchxrayvision as xrv
    except ImportError:
        raise ErrorVision('Faltan TorchXRayVision/PyTorch CPU; prepara las dependencias opcionales.') from None
    info = {'version': PREPROCESS_VERSION, **meta,
            'normalization': f'[0,{maxval}] -> [-1024,1024]', 'input_shape': [1, 1, 224, 224]}
    arreglo = xrv.datasets.normalize(arreglo, maxval)
    arreglo = xrv.datasets.XRayCenterCrop()(arreglo[None, ...])
    arreglo = xrv.datasets.XRayResizer(224)(arreglo)
    return torch.from_numpy(arreglo.astype('float32')).unsqueeze(0), info
