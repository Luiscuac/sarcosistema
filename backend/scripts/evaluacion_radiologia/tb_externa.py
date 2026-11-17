"""Evaluación externa (TB) del modelo XRV en Shenzhen + Montgomery. NO es validación clínica.

El modelo no tiene etiqueta de tuberculosis: se mide si sus categorías separan TB de normal.
Carga el mismo safetensors local que el worker una sola vez y usa el preprocesamiento de producción. Registra además si el pipeline de producción aceptaría cada archivo.
Uso (desde backend/): python -m scripts.evaluacion_radiologia.tb_externa
"""
import argparse
import json
import re
import time
from pathlib import Path

from scripts.evaluacion_radiologia.metricas import binaria

BASE_DIR = Path(__file__).resolve().parents[2]
PULMONARES = ['Atelectasis', 'Consolidation', 'Infiltration', 'Pneumothorax', 'Edema', 'Emphysema',
              'Fibrosis', 'Effusion', 'Pneumonia', 'Pleural_Thickening', 'Nodule', 'Mass',
              'Lung Lesion', 'Lung Opacity']


def lectura_clinica(texto: str) -> dict:
    """Shenzhen: 'female 28yrs\\n<lectura>'; Montgomery: 'Patient's Sex: M\\nPatient's Age: 059Y'."""
    edad = re.search(r'(\d+)\s*(yrs?|y|year|days?|month)', texto, re.I)
    edad_anios = None
    if edad:
        n, unidad = int(edad.group(1)), edad.group(2).lower()
        edad_anios = n / 365 if unidad.startswith('day') else n / 12 if unidad.startswith('month') else n
    sexo = re.search(r'\b(male|female)\b', texto, re.I) or re.search(r'Sex:\s*([MF])\b', texto)
    sexo = {'m': 'male', 'f': 'female'}.get(sexo.group(1).lower(), sexo.group(1).lower()) if sexo else None
    return {'edad': edad_anios, 'sexo': sexo, 'lectura': ' '.join(texto.split())[:300]}


def preparar(ruta: Path):
    """Usa la decodificación y el preprocesamiento de producción (PNG/JPEG/DICOM, paleta, 16 bits, >16 MP)."""
    from app.imagenes.infrastructure.vision.preprocesamiento import preparar_imagen
    tensor, info = preparar_imagen(ruta.read_bytes())
    return tensor, {'modo': info['original_mode'], 'size': info['original_size'], 'working_size': info['working_size']}


def auc_ic(y, s, repeticiones=2000, semilla=0):
    import numpy as np
    y, s = np.asarray(y), np.asarray(s)
    rng = np.random.default_rng(semilla)
    pos, neg = s[y == 1], s[y == 0]

    def auc(p, q):
        return ((p[:, None] > q[None, :]).sum() + .5 * (p[:, None] == q[None, :]).sum()) / (len(p) * len(q))
    remuestras = [auc(rng.choice(pos, len(pos)), rng.choice(neg, len(neg))) for _ in range(repeticiones)]
    return float(auc(pos, neg)), float(np.percentile(remuestras, 2.5)), float(np.percentile(remuestras, 97.5))


def _resumen_binario(y, s):
    a, lo, hi = auc_ic(y, s)
    m = binaria(y, s)
    return {'auroc': a, 'ic95': [lo, hi], 'sens@0.5': m['sensibilidad'], 'esp@0.5': m['especificidad']}


def metricas(filas: list[dict], etiquetas: list[str]) -> dict:
    y = [f['tb'] for f in filas]
    salida = {'n': len(filas), 'tb': sum(y), 'normal': len(y) - sum(y), 'por_categoria': {}}
    if not 0 < sum(y) < len(y):
        return salida
    for k in etiquetas:
        salida['por_categoria'][k] = _resumen_binario(y, [f['scores'][k] for f in filas])
    salida['max_pulmonar'] = _resumen_binario(y, [max(f['scores'][k] for k in PULMONARES) for f in filas])
    salida['media_pulmonar'] = _resumen_binario(y, [sum(f['scores'][k] for k in PULMONARES) / len(PULMONARES) for f in filas])
    return salida


def grupos(filas: list[dict]) -> dict:
    sz = [f for f in filas if f['conjunto'] == 'shenzhen']
    return {'todos': filas, 'shenzhen': sz,
            'montgomery': [f for f in filas if f['conjunto'] == 'montgomery'],
            'shenzhen_<18': [f for f in sz if f['edad'] is not None and f['edad'] < 18],
            'shenzhen_>=18': [f for f in sz if f['edad'] is not None and f['edad'] >= 18],
            'mujeres': [f for f in filas if f['sexo'] == 'female'],
            'hombres': [f for f in filas if f['sexo'] == 'male']}


def _cargar_modelo(model_dir: Path):
    import torch
    import torchxrayvision as xrv
    from safetensors.torch import load_file
    from app.imagenes.domain.vision import WEIGHTS_FILE
    meta = json.loads((model_dir / 'manifest.json').read_text(encoding='utf-8'))
    torch.set_num_threads(4)
    modelo = xrv.models.DenseNet(weights=None, op_threshs=torch.tensor(meta['op_threshs'])).cpu().eval()
    modelo.load_state_dict(load_file(str(model_dir / WEIGHTS_FILE), device='cpu'), strict=True)
    if list(modelo.targets) != meta['targets']:
        raise ValueError('Etiquetas del modelo distintas al manifiesto aprobado')
    return modelo, meta['targets']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datos', type=Path, default=BASE_DIR / '.datasets/tb-nlm')
    parser.add_argument('--salida', type=Path, default=BASE_DIR / '.datasets/tb-nlm-resultados')
    parser.add_argument('--modelos', type=Path, default=BASE_DIR / '.models/radiologia')
    args = parser.parse_args()
    import numpy as np
    import torch
    from app.imagenes.domain.vision import ImagenNoValida
    args.salida.mkdir(parents=True, exist_ok=True)
    modelo, etiquetas = _cargar_modelo(args.modelos)
    ruta_filas = args.salida / 'filas.json'
    filas = json.loads(ruta_filas.read_text(encoding='utf-8')) if ruta_filas.exists() else []
    hechos = {f['id'] for f in filas}
    imagenes = sorted((args.datos / 'shenzhen/CXR_png').glob('*.png')) + sorted((args.datos / 'montgomery/CXR_png').glob('*.png'))
    if not imagenes:
        raise SystemExit('No hay imágenes; ejecuta antes: python -m scripts.preparar_tb_nlm --descargar')
    for i, ruta in enumerate(imagenes, 1):
        if ruta.stem in hechos:
            continue
        inicio = time.perf_counter()
        # Una sola decodificación: si producción la rechaza, se registra el motivo y se omite.
        try:
            tensor, info = preparar(ruta)
            produccion = 'si'
        except ImagenNoValida as error:
            filas.append({'id': ruta.stem, 'conjunto': 'shenzhen' if ruta.stem.startswith('CHN') else 'montgomery',
                          'tb': int(ruta.stem.endswith('_1')), 'produccion': f'no: {error}'})
            continue
        with torch.inference_mode():
            salida = modelo(tensor)[0].tolist()
        conjunto = 'shenzhen' if ruta.stem.startswith('CHN') else 'montgomery'
        txt = args.datos / conjunto / 'ClinicalReadings' / (ruta.stem + '.txt')
        filas.append({'id': ruta.stem, 'conjunto': conjunto, 'tb': int(ruta.stem.endswith('_1')),
                      'scores': dict(zip(etiquetas, salida)), 'produccion': produccion, 'img': info,
                      **lectura_clinica(txt.read_text(encoding='utf-8', errors='replace') if txt.exists() else ''),
                      'segundos': time.perf_counter() - inicio})
        if i % 25 == 0 or i == len(imagenes):
            ruta_filas.write_text(json.dumps(filas), encoding='utf-8')
            print(f'{i}/{len(imagenes)}', flush=True)
    ruta_filas.write_text(json.dumps(filas), encoding='utf-8')
    resumen = {'validacion_clinica': False, 'modelo': 'densenet121-res224-all (XRV 1.5.7)',
               'nota': 'El modelo no tiene etiqueta de tuberculosis; se mide si sus categorías separan TB de normal.',
               'rechazadas_por_produccion': {c: sum(1 for f in filas if f['conjunto'] == c and f['produccion'] != 'si') for c in ('shenzhen', 'montgomery')},
               'motivos_rechazo': sorted({f['produccion'] for f in filas if f['produccion'] != 'si'}),
               'segundos_por_imagen_media': float(np.mean([f['segundos'] for f in filas if 'segundos' in f])),
               'grupos': {k: metricas(g, etiquetas) for k, g in grupos([f for f in filas if 'scores' in f]).items() if g}}
    (args.salida / 'resumen.json').write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding='utf-8')
    print('LISTO')


if __name__ == '__main__':
    main()
