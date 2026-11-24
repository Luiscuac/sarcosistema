"""Caché a 512 px (mismo preprocesamiento de producción, otro tamaño final) para modelos de mayor resolución.

Mismas imágenes y mismo orden que cache.npz (tb_cache.listar). Se escribe a disco con memmap (~5 GB) para no
cargar todo en RAM. Salida: .datasets/tb-entrenamiento/cache512_X.npy + cache512_meta.npz.
Uso (desde backend/, con .venv del sistema o .venv-gpu): python -m scripts.evaluacion_radiologia.tb_cache512
"""
import time

from scripts.evaluacion_radiologia.tb_cache import BASE_DIR, listar

LADO = 512


def main():
    import numpy as np
    import torchxrayvision as xrv
    from app.imagenes.infrastructure.vision.preprocesamiento import decodificar_radiografia
    salida = BASE_DIR / '.datasets/tb-entrenamiento'
    filas = listar(BASE_DIR / '.datasets')
    ref = np.load(salida / 'cache.npz')
    assert list(ref['id']) == [f['ruta'].stem for f in filas], 'El orden no coincide con cache.npz'
    X = np.lib.format.open_memmap(salida / 'cache512_X.npy', mode='w+', dtype=np.float16, shape=(len(filas), LADO, LADO))
    inicio = time.perf_counter()
    for i, f in enumerate(filas):
        arreglo, maxval, _ = decodificar_radiografia(f['ruta'].read_bytes())
        arreglo = xrv.datasets.normalize(arreglo, maxval)
        arreglo = xrv.datasets.XRayCenterCrop()(arreglo[None, ...])
        X[i] = xrv.datasets.XRayResizer(LADO)(arreglo)[0].astype(np.float16)
        if (i + 1) % 500 == 0:
            print(f'{i + 1}/{len(filas)} {time.perf_counter() - inicio:.0f}s', flush=True)
    X.flush()
    np.savez(salida / 'cache512_meta.npz', **{k: ref[k] for k in ref.files if k != 'X'})
    print('LISTO', len(filas))


if __name__ == '__main__':
    main()
