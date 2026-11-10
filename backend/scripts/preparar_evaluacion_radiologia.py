"""Descarga explícita, acotada, de NIH derivado; no consulta modelos."""
import argparse
import csv
import gzip
import hashlib
from importlib.util import find_spec
import json
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode, urlsplit
from urllib.error import HTTPError

BASE = Path(__file__).resolve().parents[1]
DATASET = 'chehablab/NIHChestXR'
REVISION = 'adcb330b5861dc4b1de5697e49e45ebf45d7e28c'
LABELS = ['No Finding', 'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
          'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax', 'Consolidation', 'Edema',
          'Emphysema', 'Fibrosis', 'Pleural_Thickening', 'Hernia']


def seleccionar(filas: list[dict], por_grupo: int = 15) -> list[dict]:
    seleccion, pacientes = [], set()
    for grupo in ('Consolidation', 'Effusion', 'Cardiomegaly', 'No Finding'):
        cantidad = 0
        for fila in filas:
            if fila['vista'] not in ('AP', 'PA') or fila['paciente'] in pacientes or grupo not in fila['labels']:
                continue
            seleccion.append(fila | {'estrato': grupo}); pacientes.add(fila['paciente'])
            cantidad += 1
            if cantidad == por_grupo:
                break
    return seleccion


def leer_url(url, max_bytes):
    for intento in range(3):
        try:
            with urlopen(url, timeout=45) as respuesta:
                datos = respuesta.read(max_bytes + 1)
            break
        except HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or intento == 2:
                raise
    if len(datos) > max_bytes:
        raise ValueError('Descarga supera presupuesto')
    return datos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--descargar', action='store_true', required=True)
    parser.add_argument('--output-dir', type=Path, default=BASE/'.datasets/evaluacion-fase5')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if (args.output_dir/'muestras.json').exists():
        raise SystemExit('Ya existe manifiesto; no sobrescribir')
    spec = find_spec('torchxrayvision')
    with gzip.open(Path(spec.origin).parent/'data/Data_Entry_2017_v2020.csv.gz', 'rt', encoding='utf-8-sig') as f:
        metadata = {r['Image Index']: r for r in csv.DictReader(f)}
    candidatos = []
    # Hasta 3000 filas en orden público. Sin imágenes ni inferencias para seleccionar.
    for offset in range(0, 3000, 100):
        query = urlencode(dict(dataset=DATASET, config='default', split='train', offset=offset, length=100, revision=REVISION))
        cache = args.output_dir/f'pagina-{offset:04d}.json'
        if cache.exists():
            pagina = json.loads(cache.read_text(encoding='utf-8'))
        else:
            pagina = json.loads(leer_url('https://datasets-server.huggingface.co/rows?'+query, 4*1024**2))
            cache.write_text(json.dumps(pagina), encoding='utf-8')
        for entrada in pagina['rows']:
            r = entrada['row']; nombre = f"{int(r['patient_id']):08d}_{r['scan_id']:03d}.png"
            m = metadata.get(nombre)
            if not m:
                continue
            etiquetas = m['Finding Labels'].split('|')
            if set(etiquetas) != {LABELS[i] for i in r['labels']}:
                raise ValueError('Mirror y etiquetas NIH discrepan')
            candidatos.append(dict(id=nombre, paciente=m['Patient ID'], vista=m['View Position'],
                labels=etiquetas, row_idx=entrada['row_idx'], asset_url=r['image']['src'],
                reported_dimensions=[r['image']['width'], r['image']['height']]))
        elegidos = seleccionar(candidatos)
        if len(elegidos) == 60:
            break
    # Congelar selección antes de descargar imágenes y, sobre todo, antes de inferir.
    seleccion_publica = [{k: v for k, v in r.items() if k != 'asset_url'} for r in elegidos]
    (args.output_dir/'seleccion.json').write_text(json.dumps(seleccion_publica, indent=2), encoding='utf-8')
    muestras, fallos, total = [], [], 0
    from PIL import Image
    import io
    for r in elegidos:
        try:
            if urlsplit(r['asset_url']).hostname != 'datasets-server.huggingface.co':
                raise ValueError('Host de imágenes inesperado')
            datos = leer_url(r['asset_url'], 10*1024**2); total += len(datos)
            if total > 500*1024**2:
                raise ValueError('Presupuesto global excedido')
            im = Image.open(io.BytesIO(datos)); im.verify()
            filename = r['id'].replace('.png', '.jpg')
            with (args.output_dir/filename).open('xb') as f:
                f.write(datos)
            muestras.append({'id': r['id'], 'filename': filename, 'sha256': hashlib.sha256(datos).hexdigest(),
                'patient_id': r['paciente'], 'view_from_source': r['vista'], 'reference_labels': r['labels'],
                'reference_labels_kind': 'NIH NLP weak labels; absent label treated as NLP-negative, not clinical absence',
                'synthetic': False, 'stratum': r['estrato'], 'row_idx': r['row_idx'],
                'mirror': DATASET, 'mirror_revision_requested': REVISION,
                'asset_revision_observed': urlsplit(r['asset_url']).path.split('/')[5],
                'dimensions_observed': list(im.size), 'derived_image': True,
                'attribution': 'NIH Clinical Center; Wang et al. CVPR2017; Chehab Lab mirror',
                'source': 'https://nihcc.app.box.com/v/ChestXray-NIHCC',
                'permission': 'https://cloud.google.com/healthcare-api/docs/resources/public-datasets/nih-chest#license_and_attribution'})
        except Exception as e:
            fallos.append({'id': r['id'], 'error': type(e).__name__})
    (args.output_dir/'muestras.json').write_text(json.dumps({'samples': muestras, 'errors': fallos,
        'selection': 'first rows up to 3000; deterministic stratification; distinct patients; frozen before inference',
        'independent_from_training': False, 'goal': 60, 'download_bytes': total}, indent=2), encoding='utf-8')
    print(json.dumps({'seleccionados': len(elegidos), 'descargados': len(muestras), 'errores': len(fallos), 'bytes': total}))


if __name__ == '__main__':
    main()
