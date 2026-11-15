"""Descarga explícita y reanudable de Shenzhen + Montgomery (TB) desde el servidor oficial de NLM.

Conjunto de EVALUACIÓN externa (~4,4 GB); no forma parte del producto ni se versiona.
Condiciones NLM: no compartir fuera del grupo de investigación y citar:
Jaeger S. et al., IEEE TMI 2014;33(2):233-45 y Candemir S. et al., IEEE TMI 2014;33(2):577-90.
Uso (desde backend/): python -m scripts.preparar_tb_nlm --descargar
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parents[1]
BASE = 'https://data.lhncbc.nlm.nih.gov/public/Tuberculosis-Chest-X-ray-Datasets/'
CARPETAS = {
    'shenzhen': ('Shenzhen-Hospital-CXR-Set/', ['NLM-ChinaCXRSet-ReadMe.docx', 'shenzhen_consensus_roi.csv']),
    'montgomery': ('Montgomery-County-CXR-Set/MontgomerySet/', ['NLM-MontgomeryCXRSet-ReadMe.pdf', 'montgomery_consensus_roi.csv']),
}
SUBCARPETAS = ('CXR_png/', 'ClinicalReadings/', '')
FILA = re.compile(r"<a href='([^'/]+)'>[^<]*</a></td><td class='size'>(\d+)</td>")


def parsear_indice(html: str) -> list[tuple[str, int]]:
    return [(nombre, int(tamano)) for nombre, tamano in FILA.findall(html)]


def _abrir(url):
    return urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60)


def _descargar(url, destino: Path, tamano: int):
    if destino.exists() and destino.stat().st_size == tamano:
        return
    parcial = destino.with_suffix(destino.suffix + '.part')
    for intento in range(4):
        try:
            with _abrir(url) as r, open(parcial, 'wb') as f:
                while bloque := r.read(1 << 20):
                    f.write(bloque)
            if parcial.stat().st_size != tamano:
                raise IOError('Tamaño descargado distinto al del índice oficial')
            parcial.replace(destino)
            return
        except Exception as error:
            if intento == 3:
                raise
            print(f'  reintento {intento + 1} {destino.name}: {type(error).__name__}', flush=True)
            time.sleep(3 * (intento + 1))


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        while bloque := f.read(1 << 20):
            h.update(bloque)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--descargar', action='store_true', required=True)
    parser.add_argument('--output-dir', type=Path, default=BASE_DIR / '.datasets/tb-nlm')
    args = parser.parse_args()
    manifest = {'fuente': BASE, 'condiciones': 'No compartir fuera del grupo de investigación; citar NLM/NIH (Jaeger 2014, Candemir 2014).',
                'archivos': []}
    for nombre, (prefijo, sueltos) in CARPETAS.items():
        for sub in SUBCARPETAS:
            url = BASE + prefijo + sub
            with _abrir(url + 'index.html') as r:
                entradas = parsear_indice(r.read().decode('utf-8', 'replace'))
            if not sub:
                entradas = [(n, s) for n, s in entradas if n in sueltos]
            carpeta = args.output_dir / nombre / sub
            carpeta.mkdir(parents=True, exist_ok=True)
            print(f'{nombre}/{sub}: {len(entradas)} archivos, {sum(s for _, s in entradas) / 1e9:.2f} GB', flush=True)
            for i, (archivo, tamano) in enumerate(entradas, 1):
                destino = carpeta / archivo
                _descargar(url + archivo, destino, tamano)
                manifest['archivos'].append({'ruta': f'{nombre}/{sub}{archivo}', 'bytes': tamano, 'sha256': _sha256(destino)})
                if i % 50 == 0:
                    print(f'  {i}/{len(entradas)}', flush=True)
    (args.output_dir / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    print('LISTO', len(manifest['archivos']), 'archivos')


if __name__ == '__main__':
    main()
