import hashlib
from io import BytesIO
import warnings

from app.imagenes.domain.vision import ImagenNoValida, ErrorVision, MAX_IMAGE_BYTES, PREPROCESS_VERSION


def preparar_imagen(contenido: bytes):
    if not contenido or len(contenido) > MAX_IMAGE_BYTES:
        raise ImagenNoValida('Imagen vacía o superior a 10 MiB.')
    if not contenido.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff')):
        raise ImagenNoValida('Firma de archivo no compatible con PNG/JPEG.')
    if contenido.startswith(b'\x89PNG\r\n\x1a\n') and (
            len(contenido) < 33 or contenido[8:12] != b'\x00\x00\x00\x0d'
            or contenido[12:16] != b'IHDR' or contenido[24] != 8):
        # Pillow presenta incluso RGB de 16 bits como RGB de 8: comprobar IHDR fuente.
        raise ImagenNoValida('PNG debe declarar 8 bits por canal; no se reduce precisión silenciosamente.')
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:
        raise ErrorVision('Faltan las dependencias opcionales de radiología.') from None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(contenido)) as imagen:
                if (imagen.format not in ('PNG', 'JPEG') or imagen.mode not in ('L', 'RGB')
                        or getattr(imagen, 'n_frames', 1) != 1):
                    raise ImagenNoValida('Solo PNG/JPEG de 8 bits, sin animación, escala de grises o RGB.')
                ancho, alto = imagen.size
                if min(ancho, alto) < 32 or max(ancho, alto) > 8192 or ancho * alto > 16_000_000:
                    raise ImagenNoValida('Dimensiones no admitidas: máximo 16 megapíxeles y 8192 píxeles por lado.')
                info = {'version': PREPROCESS_VERSION, 'original_size': [ancho, alto],
                        'original_mode': imagen.mode, 'format': imagen.format,
                        'original_sha256': hashlib.sha256(contenido).hexdigest(),
                        'normalization': '8-bit [0,255] -> [-1024,1024]', 'input_shape': [1, 1, 224, 224]}
                imagen.verify()
            with Image.open(BytesIO(contenido)) as imagen:
                imagen.load()
                import numpy as np
                arreglo = np.asarray(imagen).copy()
    except ImagenNoValida:
        raise
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImagenNoValida('El archivo no es una imagen admitida o está dañado.') from None
    try:
        import torch
        import torchxrayvision as xrv
    except ImportError:
        raise ErrorVision('Faltan TorchXRayVision/PyTorch CPU; prepara las dependencias opcionales.') from None
    arreglo = xrv.datasets.normalize(arreglo, 255)
    if arreglo.ndim == 3:
        arreglo = arreglo.mean(axis=2)
    arreglo = xrv.datasets.XRayCenterCrop()(arreglo[None, ...])
    arreglo = xrv.datasets.XRayResizer(224)(arreglo)
    return torch.from_numpy(arreglo).unsqueeze(0), info
