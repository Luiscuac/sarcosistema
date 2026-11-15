"""¿Los mapas de calor apuntan a la lesión? Pointing game contra regiones de radiólogos (NLM).

Para cada radiografía con TB y regiones de consenso (`*_consensus_roi.csv`, coordenadas en una
rejilla de 1024x1024 sobre la imagen original), se calcula el Grad-CAM de producción hacia el índice
pulmonar y se comprueba si su pico cae dentro de alguna región. Se compara con el azar: la
fracción del área analizada que cubren las regiones. NO es validación clínica.
Uso (desde backend/): python -m scripts.evaluacion_radiologia.tb_mapas
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from scripts.evaluacion_radiologia.tb_externa import BASE_DIR, _cargar_modelo

REJILLA = 1024


def cargar_regiones(datos: Path) -> dict[str, list[tuple[float, float, float, float]]]:
    """id -> cajas normalizadas (x, y, ancho, alto) en [0,1] respecto a la imagen original."""
    regiones = defaultdict(list)
    for conjunto in ('shenzhen', 'montgomery'):
        ruta = datos / conjunto / f'{conjunto}_consensus_roi.csv'
        if not ruta.exists():
            continue
        with open(ruta, encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                x, y, w, h = (float(fila[k]) / REJILLA for k in ('x_dis', 'y_dis', 'width_dis', 'height_dis'))
                if w > 0 and h > 0:
                    regiones[Path(fila['patientId']).stem].append((x, y, w, h))
    return dict(regiones)


def pico_en_imagen(zona: dict, region: dict) -> tuple[float, float]:
    """Pico del mapa (coordenadas del recorte central) llevado a la imagen completa normalizada."""
    return region['x'] + zona['pico']['x'] * region['ancho'], region['y'] + zona['pico']['y'] * region['alto']


def acierta(punto: tuple[float, float], cajas: list) -> bool:
    px, py = punto
    return any(x <= px <= x + w and y <= py <= y + h for x, y, w, h in cajas)


def zona_toca(zona: dict, region: dict, cajas: list) -> bool:
    """¿La zona más activa (llevada a la imagen completa) se superpone con alguna región?"""
    zx, zy = region['x'] + zona['x'] * region['ancho'], region['y'] + zona['y'] * region['alto']
    zw, zh = zona['ancho'] * region['ancho'], zona['alto'] * region['alto']
    return any(zx < x + w and x < zx + zw and zy < y + h and y < zy + zh for x, y, w, h in cajas)


def fraccion_azar(cajas: list, region: dict, muestras: int = 4000, semilla: int = 0) -> float:
    """Probabilidad de acertar con un punto al azar dentro del área que analiza el modelo."""
    import numpy as np
    rng = np.random.default_rng(semilla)
    xs = region['x'] + rng.random(muestras) * region['ancho']
    ys = region['y'] + rng.random(muestras) * region['alto']
    return float(np.mean([acierta((x, y), cajas) for x, y in zip(xs, ys)]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datos', type=Path, default=BASE_DIR / '.datasets/tb-nlm')
    parser.add_argument('--salida', type=Path, default=BASE_DIR / '.datasets/tb-nlm-resultados/mapas_tb.json')
    parser.add_argument('--modelos', type=Path, default=BASE_DIR / '.models/radiologia')
    parser.add_argument('--mascara-pulmonar', action='store_true', help='Limita el mapa a los pulmones (segmentación local)')
    args = parser.parse_args()
    import numpy as np
    from app.imagenes.infrastructure.vision.explicacion import mapas_calor, region_del_mapa
    from app.imagenes.infrastructure.vision.preprocesamiento import preparar_imagen
    from app.imagenes.infrastructure.vision.worker import _objetivos_mapas, resultado_enriquecido
    modelo, targets = _cargar_modelo(args.modelos)
    segmentador = None
    if args.mascara_pulmonar:
        from app.imagenes.infrastructure.vision.segmentacion import cargar_segmentador, mascara_pulmonar
        segmentador = cargar_segmentador()
        if segmentador is None:
            raise SystemExit('Prepara antes: python -m scripts.preparar_segmentacion_pulmonar --descargar')
    regiones = cargar_regiones(args.datos)
    filas = []
    for i, (caso, cajas) in enumerate(sorted(regiones.items()), 1):
        conjunto = 'shenzhen' if caso.startswith('CHN') else 'montgomery'
        tensor, info = preparar_imagen((args.datos / conjunto / 'CXR_png' / f'{caso}.png').read_bytes())
        import torch
        with torch.inference_mode():
            scores = dict(zip(targets, modelo(tensor)[0].tolist()))
        enriquecido = resultado_enriquecido(scores, targets)
        objetivos = _objetivos_mapas(targets, enriquecido['all_findings'])
        mascara = mascara_pulmonar(segmentador, tensor) if segmentador is not None else None
        mapa = mapas_calor(modelo, tensor, {'indice_pulmonar': objetivos['indice_pulmonar']}, mascara)['indice_pulmonar']
        region = region_del_mapa(info['working_size'])
        fila = {'id': caso, 'conjunto': conjunto, 'regiones': len(cajas), 'indice': enriquecido['indice_pulmonar']['valor'],
                'azar': fraccion_azar(cajas, region)}
        if mapa['zona']:
            pico = pico_en_imagen(mapa['zona'], region)
            fila |= {'acierto': acierta(pico, cajas), 'zona_toca': zona_toca(mapa['zona'], region, cajas),
                     'pico': pico, 'zona_area': mapa['zona']['ancho'] * mapa['zona']['alto']}
        filas.append(fila)
        if i % 20 == 0:
            print(f'{i}/{len(regiones)}', flush=True)
    resumen = {'validacion_clinica': False, 'objetivo': 'Grad-CAM hacia el índice pulmonar (producción)',
               'mascara_pulmonar': bool(segmentador),
               'referencia': 'Regiones de consenso NLM (Shenzhen, Montgomery); rejilla 1024x1024 verificada visualmente.'}
    for nombre, grupo in (('todos', filas), ('shenzhen', [f for f in filas if f['conjunto'] == 'shenzhen']),
                          ('montgomery', [f for f in filas if f['conjunto'] == 'montgomery'])):
        validos = [f for f in grupo if 'acierto' in f]
        if validos:
            resumen[nombre] = {'n': len(validos), 'aciertos': sum(f['acierto'] for f in validos),
                               'tasa_acierto': float(np.mean([f['acierto'] for f in validos])),
                               'tasa_azar_media': float(np.mean([f['azar'] for f in validos])),
                               'tasa_zona_toca': float(np.mean([f['zona_toca'] for f in validos])),
                               'area_zona_media': float(np.mean([f['zona_area'] for f in validos])),
                               'picos_tercio_inferior': float(np.mean([f['pico'][1] > 2 / 3 for f in validos]))}
    args.salida.write_text(json.dumps({'resumen': resumen, 'filas': filas}, indent=1), encoding='utf-8')
    print(json.dumps(resumen, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
