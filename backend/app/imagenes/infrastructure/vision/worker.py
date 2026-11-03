"""Trabajador efímero CPU: solo safetensors locales, sin clientes ni descargas."""
from importlib.metadata import version
import time

from app.imagenes.domain.vision import (
    ErrorVision, SELECTED_TARGETS, XRV_VERSION, WEIGHTS_FILE, SCORE_KIND,
)
from app.imagenes.infrastructure.vision.artefactos import comprobar_artefactos
from app.imagenes.infrastructure.vision.preprocesamiento import preparar_imagen
from app.imagenes.infrastructure.vision.recursos import verificar_memoria


def inferir(contenido: bytes, config, proyeccion: str, repeticiones: int) -> dict:
    inicio = time.perf_counter()
    libre = verificar_memoria(config.min_free_bytes)
    metadata = comprobar_artefactos(config.model_dir)
    if version('torchxrayvision') != XRV_VERSION:
        raise ErrorVision('La versión de TorchXRayVision no coincide con la preparación local.')
    import torch
    import torchxrayvision as xrv
    from safetensors.torch import load_file
    import psutil
    torch.set_num_threads(config.threads)
    torch.set_num_interop_threads(1)
    carga = time.perf_counter()
    # weights=None es intencionado: NO se invoca get_weights ni resolución de URLs.
    modelo = xrv.models.DenseNet(weights=None, op_threshs=torch.tensor(metadata['op_threshs'])).cpu().eval()
    modelo.load_state_dict(load_file(str(config.model_dir / WEIGHTS_FILE), device='cpu'), strict=True)
    if list(modelo.targets) != metadata['targets']:
        raise ErrorVision('Las etiquetas del runtime no coinciden con el artefacto aprobado.')
    carga_s = time.perf_counter() - carga
    pre = time.perf_counter()
    tensor, info = preparar_imagen(contenido)
    pre_s = time.perf_counter() - pre
    duraciones = []
    with torch.inference_mode():
        for _ in range(repeticiones):
            t = time.perf_counter()
            salida = modelo(tensor)
            duraciones.append(time.perf_counter() - t)
    if salida.shape != (1, len(metadata['targets'])) or not torch.isfinite(salida).all():
        raise ErrorVision('El modelo devolvió una salida visual incompatible.')
    valores = salida[0].tolist()
    if any(v < 0 or v > 1 for v in valores):
        raise ErrorVision('Puntuaciones fuera del contrato de salida del modelo.')
    por_nombre = dict(zip(metadata['targets'], valores))
    return {
        'model': metadata['model'], 'model_version': metadata['xrv_version'],
        'torch_version': torch.__version__, 'weights_sha256': metadata['weights_sha256'],
        'labels_supported': metadata['targets'], 'device': 'cpu', 'threads': config.threads,
        'experimental': True, 'calibrated_probability': False, 'score_kind': SCORE_KIND,
        'findings': [{'name': nombre, 'score': por_nombre[nombre]} for nombre in SELECTED_TARGETS],
        'projection_declared': proyeccion, 'preprocessing': info,
        'warnings': ['Puntuaciones experimentales, no probabilidades clínicas calibradas ni diagnósticos.',
                     'Solo se evalúan tres categorías; una puntuación baja no demuestra normalidad ni descarta enfermedad.'],
        'metrics': {'model_load_seconds': carga_s, 'preprocessing_seconds': pre_s,
            'inference_seconds': duraciones, 'worker_total_seconds': time.perf_counter() - inicio,
            'available_bytes_before_model': libre, 'worker_rss_at_end_bytes': psutil.Process().memory_info().rss},
    }


def ejecutar_worker(conexion, contenido, config, proyeccion, repeticiones):
    try:
        conexion.send({'ok': True, 'result': inferir(contenido, config, proyeccion, repeticiones)})
    except ErrorVision as error:
        conexion.send({'ok': False, 'kind': type(error).__name__, 'message': str(error)})
    except Exception:
        # No filtrar contenido, rutas de imagen ni detalles internos del runtime.
        conexion.send({'ok': False, 'kind': 'ErrorVision', 'message': 'No se pudo ejecutar el modelo visual CPU. Comprueba dependencias y artefactos locales.'})
    finally:
        conexion.close()
