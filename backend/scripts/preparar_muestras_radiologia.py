"""Preparar DOS PNG NIH desidentificados distribuidos como muestras por XRV.

Permisos/atribución: https://cloud.google.com/healthcare-api/docs/resources/public-datasets/nih-chest
No descarga el dataset completo ni inventa informes emparejados.
"""
import argparse
import csv
import gzip
from importlib.util import find_spec
import json
from pathlib import Path

from scripts.preparar_modelos_radiologia import descargar_archivo
from app.imagenes.infrastructure.vision.artefactos import sha256_archivo

SOURCE_REVISION = '17726dd8f5e756eec3e5ae958281a289b05b1dae'
SAMPLES = (
    ('NIH-RX-001', '00000001_000.png', 'NIH-RX-001.png'),
    ('NIH-RX-002', '00027426_000.png', 'NIH-RX-002.png'),
)
DEFAULT_DIR = Path(__file__).resolve().parents[1] / '.datasets' / 'radiologia'
PERMISSION = 'https://cloud.google.com/healthcare-api/docs/resources/public-datasets/nih-chest#license_and_attribution'
ATTRIBUTION = ('Data provider: NIH Clinical Center. Xiaosong Wang, Yifan Peng, Le Lu, Zhiyong Lu, '
    'Mohammadhadi Bagheri, Ronald Summers. ChestX-ray8: Hospital-scale Chest X-ray Database and '
    'Benchmarks on Weakly-Supervised Classification and Localization of Common Thorax Diseases. '
    'IEEE CVPR, 3462-3471, 2017.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_DIR)
    parser.add_argument('--descargar', action='store_true')
    args = parser.parse_args()
    if not args.descargar:
        raise SystemExit('Las muestras solo se descargan durante preparación explícita con --descargar.')
    spec = find_spec('torchxrayvision')
    if spec is None:
        raise SystemExit('Instala antes las dependencias opcionales de radiología.')
    tabla = Path(spec.origin).parent / 'data' / 'Data_Entry_2017_v2020.csv.gz'
    buscadas = {imagen for _, imagen, _ in SAMPLES}
    with gzip.open(tabla, 'rt', encoding='utf-8-sig') as archivo:
        metadata = {fila['Image Index']: fila for fila in csv.DictReader(archivo) if fila['Image Index'] in buscadas}
    if metadata.keys() != buscadas:
        raise SystemExit('No se localizaron los metadatos de las dos muestras; revisar procedencia.')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = args.output_dir / 'muestras.json'
    if manifest.exists():
        raise SystemExit('El manifest ya existe; no se sobrescribió.')
    entradas = []
    for id, original, nombre in SAMPLES:
        url = f'https://raw.githubusercontent.com/mlmed/torchxrayvision/{SOURCE_REVISION}/tests/{original}'
        destino = args.output_dir / nombre
        descargar_archivo(url, destino, 10 * 1024**2)
        entradas.append({'id': id, 'filename': nombre, 'sha256': sha256_archivo(destino),
            'download_url': url, 'source_revision': SOURCE_REVISION, 'source_image_id': original,
            'dataset_source': 'https://nihcc.app.box.com/v/ChestXray-NIHCC',
            'permission_reference': PERMISSION, 'license': 'NIH: use permitted with attribution',
            'attribution': ATTRIBUTION, 'view_from_source': metadata[original]['View Position'],
            'synthetic': False, 'reference_labels': metadata[original]['Finding Labels'].split('|'),
            'reference_labels_kind': 'NIH weak labels; not expert adjudication',
            'identifier_review': 'pending_visual_review', 'paired_radiology_report': None,
            'note': 'Real radiograph distributed as XRV test fixture; not an independent evaluation set.'})
    manifest.write_text(json.dumps({'samples': entradas}, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Dos muestras NIH preparadas con atribución. Revisar identificadores visualmente antes de analizar. No son una evaluación clínica independiente.')


if __name__ == '__main__':
    main()
