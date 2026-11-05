import hashlib
import json
import math
from pathlib import Path

from app.imagenes.domain.vision import (
    ErrorVision, ModeloNoPreparado, MODEL_ID, XRV_VERSION, TARGETS,
    WEIGHTS_FILE, PREPROCESS_VERSION, SCORE_KIND,
)


def sha256_archivo(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b''):
            digest.update(bloque)
    return digest.hexdigest()


def comprobar_artefactos(carpeta: Path) -> dict:
    carpeta = Path(carpeta)
    manifest = carpeta / 'manifest.json'
    if not manifest.is_file():
        raise ModeloNoPreparado('Modelo local ausente. Ejecuta scripts.preparar_modelos_radiologia durante la preparación.')
    try:
        if manifest.stat().st_size > 32000:
            raise ValueError
        datos = json.loads(manifest.read_text(encoding='utf-8'))
        if (not isinstance(datos, dict) or datos.get('model') != MODEL_ID
                or datos.get('xrv_version') != XRV_VERSION
                or datos.get('targets') != list(TARGETS)
                or datos.get('preprocessing') != PREPROCESS_VERSION
                or datos.get('score_kind') != SCORE_KIND):
            raise ValueError
        umbrales = datos['op_threshs']
        if len(umbrales) != len(TARGETS) or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 < v < 1 for v in umbrales):
            raise ValueError
        peso = carpeta / WEIGHTS_FILE
        if not peso.is_file():
            raise ModeloNoPreparado('Faltan pesos locales; ejecuta scripts.preparar_modelos_radiologia fuera de las solicitudes clínicas.')
        if not 1024 < peso.stat().st_size < 100 * 1024**2 or sha256_archivo(peso) != datos['weights_sha256']:
            raise ErrorVision('La integridad de los pesos locales no coincide. No se descargó ningún archivo.')
        return datos
    except ModeloNoPreparado:
        raise
    except ErrorVision:
        raise
    except (OSError, ValueError, TypeError, KeyError):
        raise ErrorVision('El manifest del modelo local es incompatible o no se puede validar.') from None
