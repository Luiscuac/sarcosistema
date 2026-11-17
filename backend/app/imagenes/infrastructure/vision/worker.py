"""Trabajador efímero CPU: solo safetensors locales, sin clientes ni descargas."""
from importlib.metadata import version
import time

from app.imagenes.domain.vision import (
    ErrorVision, SELECTED_TARGETS, XRV_VERSION, WEIGHTS_FILE, SCORE_KIND,
)
from app.imagenes.infrastructure.vision.artefactos import comprobar_artefactos
from app.imagenes.infrastructure.vision.preprocesamiento import preparar_imagen
from app.imagenes.infrastructure.vision.recursos import verificar_memoria

ADVERTENCIAS = [
    'Puntuaciones experimentales, no probabilidades clínicas calibradas ni diagnósticos.',
    'El modelo evalúa 18 categorías y no cubre todas las patologías; una puntuación o índice bajo no descarta enfermedad.',
    'La comparación con el informe es por reglas de texto: puede no entender redacciones poco habituales.',
    'Los mapas de calor muestran dónde se apoyó el modelo, no la ubicación confirmada de una lesión.',
]
MAPAS_CATEGORIAS = 3


def resultado_enriquecido(por_nombre: dict, targets: list) -> dict:
    """18 categorías ordenadas + índice pulmonar. Puro: sin torch."""
    from app.imagenes.infrastructure.vision.indice import calcular_indice
    todas = sorted(({'name': n, 'score': por_nombre[n], 'above_operating_point': por_nombre[n] >= 0.5} for n in targets),
                   key=lambda h: h['score'], reverse=True)
    return {'all_findings': todas, 'indice_pulmonar': calcular_indice(por_nombre)}


def _objetivos_mapas(targets: list, todas: list):
    import torch
    from app.imagenes.infrastructure.vision.indice import cargar_indice
    a = cargar_indice()
    posicion = {n: i for i, n in enumerate(targets)}
    w = torch.tensor(a['coeficientes']) / torch.tensor(a['desviacion'])
    m = torch.tensor(a['media'])
    orden = torch.tensor([posicion[n] for n in a['etiquetas']])
    objetivos = {'indice_pulmonar': lambda s: (w * (s[orden] - m)).sum()}
    for h in todas[:MAPAS_CATEGORIAS]:
        objetivos[h['name']] = (lambda i: lambda s: s[i])(posicion[h['name']])
    return objetivos


def inferir(contenido: bytes, config, proyeccion: str, repeticiones: int, explicar: bool = True) -> dict:
    inicio = time.perf_counter()
    libre = verificar_memoria(config.min_free_bytes)
    metadata = comprobar_artefactos(config.model_dir)
    if version('torchxrayvision') != XRV_VERSION:
        raise ErrorVision('La versión de TorchXRayVision no coincide con la preparación local.')
    import torch
    import torchxrayvision as xrv
    from safetensors.torch import load_file
    import psutil
    from app.imagenes.infrastructure.vision.explicacion import agregar_aviso_pulmonar, evaluar_calidad, mapas_calor, region_del_mapa
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
    enriquecido = resultado_enriquecido(por_nombre, metadata['targets'])
    plano = tensor.numpy()
    calidad = evaluar_calidad(info, float(plano.std()), float(((plano <= -1020) | (plano >= 1020)).mean()), proyeccion)
    explicar_s, mapas, mascara = 0.0, {}, None
    if explicar:
        t = time.perf_counter()
        if getattr(config, 'mascara_pulmonar', False):
            from app.imagenes.infrastructure.vision.segmentacion import cargar_segmentador, mascara_pulmonar
            segmentador = cargar_segmentador()
            if segmentador is not None:
                mascara = mascara_pulmonar(segmentador, tensor)
                del segmentador
                agregar_aviso_pulmonar(calidad, float(mascara.mean()))
        mapas = mapas_calor(modelo, tensor, _objetivos_mapas(metadata['targets'], enriquecido['all_findings']), mascara)
        explicar_s = time.perf_counter() - t
    return {
        'model': metadata['model'], 'model_version': metadata['xrv_version'],
        'torch_version': torch.__version__, 'weights_sha256': metadata['weights_sha256'],
        'labels_supported': metadata['targets'], 'device': 'cpu', 'threads': config.threads,
        'experimental': True, 'calibrated_probability': False, 'score_kind': SCORE_KIND,
        'findings': [{'name': nombre, 'score': por_nombre[nombre]} for nombre in SELECTED_TARGETS],
        **enriquecido, 'calidad': calidad,
        'mapas_calor': {'region': region_del_mapa(info['working_size']), 'mapas': mapas,
                        'restringido_a_pulmones': mascara is not None} if mapas else None,
        'projection_declared': proyeccion, 'preprocessing': info,
        'warnings': list(ADVERTENCIAS),
        'metrics': {'model_load_seconds': carga_s, 'preprocessing_seconds': pre_s,
            'inference_seconds': duraciones, 'explanation_seconds': explicar_s,
            'worker_total_seconds': time.perf_counter() - inicio,
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
