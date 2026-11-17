"""Prepara (online, explícito) la segmentación anatómica PSPNet de TorchXRayVision para limitar
los mapas de calor a los campos pulmonares. Runtime: solo safetensors local verificado.

Fuente: ChestX-Det (Deepwise AI Lab) vía TorchXRayVision 1.5.7, 14 estructuras anatómicas.
Uso (desde backend/): python -m scripts.preparar_segmentacion_pulmonar --descargar
"""
import argparse
import json
from pathlib import Path

from scripts.preparar_modelos_radiologia import descargar_archivo
from app.imagenes.infrastructure.vision.artefactos import sha256_archivo
from app.imagenes.infrastructure.vision.segmentacion import (
    DIRECTORIO, ESTRUCTURAS, MANIFIESTO, PESOS, construir_modelo,
)

URL = 'https://github.com/mlmed/torchxrayvision/releases/download/v1/pspnet_chestxray_best_model_4.pth'
MAX_BYTES = 300 * 1024**2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--descargar', action='store_true', required=True)
    parser.add_argument('--model-dir', type=Path, default=DIRECTORIO)
    args = parser.parse_args()
    if (args.model_dir / MANIFIESTO).exists():
        raise SystemExit('La segmentación ya está preparada; no se sobrescribe.')
    import torch
    from safetensors.torch import save_file
    checkpoint = args.model_dir / 'pspnet_chestxray_best_model_4.pth'
    descargar_archivo(URL, checkpoint, MAX_BYTES)
    try:
        # weights_only=True: no se ejecuta código del archivo descargado.
        estado = torch.load(checkpoint, map_location='cpu', weights_only=True)
        estado = {(k[7:] if k.startswith('module.') else k): v.contiguous() for k, v in estado.items()}
        modelo = construir_modelo()
        modelo.load_state_dict(estado, strict=True)
        save_file(estado, str(args.model_dir / PESOS))
        verificacion = construir_modelo()
        from safetensors.torch import load_file
        verificacion.load_state_dict(load_file(str(args.model_dir / PESOS), device='cpu'), strict=True)
        (args.model_dir / MANIFIESTO).write_text(json.dumps({
            'model': 'chestx-det-pspnet', 'source_url': URL, 'checkpoint_sha256': sha256_archivo(checkpoint),
            'weights_file': PESOS, 'weights_sha256': sha256_archivo(args.model_dir / PESOS),
            'targets': list(ESTRUCTURAS), 'xrv_version': '1.5.7',
            'uso': 'Restringir mapas de calor a los campos pulmonares; no diagnostica.'}, indent=1), encoding='utf-8')
    finally:
        checkpoint.unlink(missing_ok=True)  # el pickle original no se conserva
    print('Segmentación pulmonar preparada en safetensors con manifiesto SHA-256.')


if __name__ == '__main__':
    main()
