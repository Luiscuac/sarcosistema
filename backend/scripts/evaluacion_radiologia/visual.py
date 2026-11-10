"""Benchmark contra etiquetas débiles NIH, NO validación clínica."""
import hashlib
import json
from pathlib import Path
from scripts.evaluacion_radiologia.casos import TERMINOS
from scripts.evaluacion_radiologia.metricas import binaria


def etiquetas_binarias(labels):
    return {k: None if labels is None else int(k in labels) for k in TERMINOS}


def validar_muestra(muestra, raiz):
    nombre = muestra['filename']
    if Path(nombre).name != nombre or muestra['view_from_source'] not in ('AP', 'PA'):
        raise ValueError('Muestra incompatible')
    datos = (raiz/nombre).read_bytes()
    if hashlib.sha256(datos).hexdigest() != muestra['sha256']:
        raise ValueError('Hash incompatible')
    return datos


def denominadores(manifest, filas):
    disponibles = len(manifest['samples'])
    perdidas = len(manifest.get('errors', []))
    errores = sum('error' in r for r in filas)
    return {'n_seleccionados': disponibles+perdidas, 'n_descargas_fallidas': perdidas,
        'n_disponibles': disponibles, 'n_intentos': len(filas),
        'n_completados': sum('result' in r for r in filas), 'n_errores': errores,
        'n_perdidas_totales': perdidas+errores}


def evaluar_visual(manifest: Path, model_dir: Path, salida: Path, min_free_mib=2048) -> dict:
    from app.imagenes.domain.vision import VisionConfig
    from app.imagenes.infrastructure.vision.servicio import AnalizadorTorax
    preparacion = json.loads(manifest.read_text(encoding='utf-8'))
    muestras = preparacion['samples']
    if len({m.get('patient_id', m['id']) for m in muestras}) != len(muestras):
        raise ValueError('Pacientes duplicados')
    servicio = AnalizadorTorax(VisionConfig(model_dir, min_free_bytes=min_free_mib*1024**2))
    resultados = []
    for m in muestras:
        fila = {'id': m['id'], 'reference': etiquetas_binarias(m.get('reference_labels'))}
        try:
            datos = validar_muestra(m, manifest.parent)
            fila['result'] = servicio.analizar(datos, proyeccion=m['view_from_source'])
        except Exception as e:
            fila['error'] = type(e).__name__
        resultados.append(fila)
        # Checkpoint por imagen: no perder resultados si se interrumpe el lote.
        salida.write_text(json.dumps({'rows': resultados}, indent=2), encoding='utf-8')
    correctos = [r for r in resultados if 'result' in r]
    metricas = {k: binaria([r['reference'][k] for r in correctos],
        [next(f['score'] for f in r['result']['findings'] if f['name'] == k) for r in correctos]) for k in TERMINOS}
    r = {'validacion_clinica': False, 'independent_from_training': False, **denominadores(preparacion, resultados),
        'errores_preparacion': preparacion.get('errors', []),
        'negative_policy': 'NLP label not present = weak negative only; unknown metadata excluded',
        'metricas': metricas, 'rows': resultados}
    salida.write_text(json.dumps(r, indent=2), encoding='utf-8')
    return r
