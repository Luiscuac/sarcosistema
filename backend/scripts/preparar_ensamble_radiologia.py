"""Prepara (online, explícito) los 6 DenseNet XRV especialistas del ensamble del patrón TB.

Fuente: releases oficiales de TorchXRayVision 1.5.7 (HTTPS). Cada checkpoint se convierte a safetensors, se verifica
que la salida coincide con la del oficial, se registra su SHA-256 en el manifiesto y se BORRA el pickle original.
Runtime: solo safetensors verificados (app/imagenes/infrastructure/vision/ensamble.py).
Uso (desde backend/): python -m scripts.preparar_ensamble_radiologia --descargar
"""
import argparse
import gc
import json
import math
import os
from importlib.metadata import version
from pathlib import Path

from app.imagenes.domain.vision import XRV_VERSION
from app.imagenes.infrastructure.vision.artefactos import sha256_archivo
from app.imagenes.infrastructure.vision.ensamble import DIRECTORIO, MANIFIESTO, MODELOS
from scripts.preparar_modelos_radiologia import descargar_archivo

MAX_BYTES = 40 * 1024**2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--descargar', action='store_true', required=True)
    parser.add_argument('--model-dir', type=Path, default=DIRECTORIO)
    args = parser.parse_args()
    if (args.model_dir / MANIFIESTO).exists():
        raise SystemExit('El ensamble ya está preparado; no se sobrescribe.')
    if version('torchxrayvision') != XRV_VERSION:
        raise SystemExit('La versión instalada de TorchXRayVision no es la prevista.')
    import torch
    import torchxrayvision as xrv
    from safetensors.torch import load_file, save_file
    torch.set_num_threads(4)
    args.model_dir.mkdir(parents=True, exist_ok=True)
    prueba = torch.linspace(-1024, 1024, 224 * 224).reshape(1, 1, 224, 224)
    modelos = {}
    for nombre in MODELOS:
        info = xrv.models.model_urls[f'densenet121-res224-{nombre}']
        checkpoint = args.model_dir / os.path.basename(info['weights_url'])
        descargar_archivo(info['weights_url'], checkpoint, MAX_BYTES)
        try:
            sha_checkpoint = sha256_archivo(checkpoint)
            # Solo en preparación: checkpoint oficial de confianza (cache_dir local, sin red: ya existe).
            original = xrv.models.DenseNet(weights=f'densenet121-res224-{nombre}', cache_dir=str(args.model_dir)).cpu().eval()
            umbrales = [None if math.isnan(u) else float(u) for u in original.op_threshs.tolist()]
            with torch.inference_mode():
                referencia = original(prueba).clone()
            pesos = args.model_dir / f'densenet121-res224-{nombre}.safetensors'
            save_file({k: v.detach().cpu().contiguous() for k, v in original.state_dict().items()}, str(pesos))
            del original
            gc.collect()
            local = xrv.models.DenseNet(weights=None, op_threshs=torch.tensor([math.nan if u is None else u for u in umbrales])).cpu().eval()
            local.load_state_dict(load_file(str(pesos), device='cpu'), strict=True)
            with torch.inference_mode():
                conversion = local(prueba)
            validas = torch.isfinite(referencia)
            if not torch.equal(validas, torch.isfinite(conversion)) or not torch.allclose(referencia[validas], conversion[validas], rtol=1e-6, atol=1e-7):
                raise SystemExit(f'La conversión de {nombre} no conserva la salida del modelo oficial.')
            modelos[nombre] = {'weights_file': pesos.name, 'weights_sha256': sha256_archivo(pesos),
                               'checkpoint_url': info['weights_url'], 'checkpoint_sha256': sha_checkpoint,
                               'targets': list(info['labels']), 'op_threshs': umbrales}
            print('preparado', nombre, flush=True)
        finally:
            checkpoint.unlink(missing_ok=True)  # el pickle original no se conserva
    (args.model_dir / MANIFIESTO).write_text(json.dumps({
        'schema_version': 1, 'xrv_version': XRV_VERSION, 'torch_preparation_version': torch.__version__,
        'uso': 'Solo para el patrón TB (promedio con el modelo base); no se usa en el índice ni en las 18 categorías.',
        'license_reference': 'https://github.com/mlmed/torchxrayvision/blob/main/LICENSE', 'modelos': modelos}, indent=1), encoding='utf-8')
    print('Ensamble preparado en safetensors con manifiesto SHA-256.')


if __name__ == '__main__':
    main()
