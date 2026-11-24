"""Prepara la caché de entrenamiento/prueba de TB con el preprocesamiento de PRODUCCIÓN. NO es validación clínica.

Fuentes (cada una es un "sitio" distinto para probar en hospitales no vistos):
- tbx11k: TBX11K (China) listas oficiales TBX11K_train / TBX11K_val. Clases sano / enfermo-no-TB / TB.
  Se EXCLUYE imgs/extra/mc+shenzhen (son copias de Shenzhen/Montgomery, que se usan como prueba externa).
- dadb: DA+DB (India) incluidos en TBX11K/imgs/extra/da+db (p*/px* = TB, n*/nx* = sin TB).
- shenzhen, montgomery: originales NLM de backend/.datasets/tb-nlm (sufijo _1 = TB).

Salida: .datasets/tb-entrenamiento/cache.npz con X (float16, N x 224 x 224, ya normalizado como producción),
tb, clase, sitio, particion, id.
Uso (desde backend/, con .venv del sistema): python -m scripts.evaluacion_radiologia.tb_cache
"""
import argparse
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CLASES = {'health': 'sano', 'sick': 'enfermo_no_tb', 'tb': 'tb'}


def listar(datos: Path) -> list[dict]:
    tbx = datos / 'tbx11k/TBX11K'
    filas = []
    for particion in ('train', 'val'):
        for linea in (tbx / f'lists/TBX11K_{particion}.txt').read_text().split():
            carpeta = linea.split('/')[0]
            filas.append({'ruta': tbx / 'imgs' / linea, 'sitio': 'tbx11k', 'particion': particion,
                          'clase': CLASES[carpeta], 'tb': int(carpeta == 'tb')})
    for ruta in sorted((tbx / 'imgs/extra/da+db').rglob('*.png')):
        tb = int(ruta.stem.startswith('p'))
        filas.append({'ruta': ruta, 'sitio': 'dadb', 'particion': 'externa',
                      'clase': 'tb' if tb else 'sin_tb', 'tb': tb})
    for sitio in ('shenzhen', 'montgomery'):
        for ruta in sorted((datos / 'tb-nlm' / sitio / 'CXR_png').glob('*.png')):
            tb = int(ruta.stem.endswith('_1'))
            filas.append({'ruta': ruta, 'sitio': sitio, 'particion': 'externa',
                          'clase': 'tb' if tb else 'sin_tb', 'tb': tb})
    return filas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datos', type=Path, default=BASE_DIR / '.datasets')
    parser.add_argument('--salida', type=Path, default=BASE_DIR / '.datasets/tb-entrenamiento')
    args = parser.parse_args()
    import numpy as np
    from app.imagenes.infrastructure.vision.preprocesamiento import preparar_imagen
    filas = listar(args.datos)
    X = np.zeros((len(filas), 224, 224), dtype=np.float16)
    inicio = time.perf_counter()
    for i, f in enumerate(filas):
        tensor, _ = preparar_imagen(f['ruta'].read_bytes())
        X[i] = tensor.numpy()[0, 0].astype(np.float16)
        if (i + 1) % 500 == 0:
            print(f'{i + 1}/{len(filas)} {time.perf_counter() - inicio:.0f}s', flush=True)
    args.salida.mkdir(parents=True, exist_ok=True)
    np.savez(args.salida / 'cache.npz', X=X,
             tb=np.array([f['tb'] for f in filas], dtype=np.int8),
             clase=np.array([f['clase'] for f in filas]), sitio=np.array([f['sitio'] for f in filas]),
             particion=np.array([f['particion'] for f in filas]),
             id=np.array([f['ruta'].stem for f in filas]))
    from collections import Counter
    print(Counter((f['sitio'], f['particion'], f['clase']) for f in filas))
    print('LISTO', len(filas))


if __name__ == '__main__':
    main()
