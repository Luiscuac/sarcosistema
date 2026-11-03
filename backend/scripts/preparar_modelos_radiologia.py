"""Preparación EXPLÍCITA con Internet. La inferencia nunca importa este módulo."""
import argparse
import gc
from importlib.metadata import version
import json
from pathlib import Path
from urllib.parse import urlsplit

from app.imagenes.domain.vision import (
    MODEL_ID, XRV_VERSION, TARGETS, WEIGHTS_FILE, PREPROCESS_VERSION, SCORE_KIND,
    ModeloNoPreparado, ErrorVision,
)
from app.imagenes.infrastructure.vision.artefactos import sha256_archivo, comprobar_artefactos
from app.imagenes.infrastructure.vision.recursos import verificar_memoria

DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[1] / '.models' / 'radiologia'
CHECKPOINT = 'nih-pc-chex-mimic_ch-google-openi-kaggle-densenet121-d121-tw-lr001-rot45-tr15-sc15-seed0-best.pt'
WEIGHTS_URL = 'https://github.com/mlmed/torchxrayvision/releases/download/v1/' + CHECKPOINT


def descargar_archivo(url: str, destino: Path, max_bytes: int) -> None:
    if urlsplit(url).scheme != 'https':
        raise ValueError('La preparación solo admite fuentes HTTPS explícitas.')
    destino = Path(destino)
    if destino.exists():
        raise FileExistsError('No se sobrescribe un artefacto existente.')
    import httpx
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + '.part')
    creado = False
    try:
        with parcial.open('xb') as archivo:
            creado = True
            with httpx.stream('GET', url, follow_redirects=True, timeout=90,
                    headers={'User-Agent': 'SarcoSistemaResearchPrototype/0.1 (local academic demo)'}) as respuesta:
                respuesta.raise_for_status()
                total = 0
                for bloque in respuesta.iter_bytes():
                    total += len(bloque)
                    if total > max_bytes:
                        raise ValueError('El recurso supera el tamaño permitido.')
                    archivo.write(bloque)
        parcial.replace(destino)
    finally:
        if creado:
            parcial.unlink(missing_ok=True)


def preparar(carpeta: Path, permitir_descarga: bool = False) -> dict:
    carpeta = Path(carpeta)
    if (carpeta / 'manifest.json').exists():
        return comprobar_artefactos(carpeta)
    verificar_memoria(4 * 1024**3)
    if version('torchxrayvision') != XRV_VERSION:
        raise ErrorVision('La versión instalada de TorchXRayVision no es la prevista.')
    checkpoint = carpeta / CHECKPOINT
    recibo = carpeta / 'checkpoint-procedencia.json'
    if not checkpoint.exists():
        if not permitir_descarga:
            raise ModeloNoPreparado('Usa --descargar solo durante la preparación autorizada con Internet.')
        descargar_archivo(WEIGHTS_URL, checkpoint, 40 * 1024**2)
        if checkpoint.stat().st_size != 28_382_008:
            raise ErrorVision('El tamaño del checkpoint oficial cambió; revisar antes de cargarlo.')
        recibo.write_text(json.dumps({'url': WEIGHTS_URL, 'sha256': sha256_archivo(checkpoint)}, indent=2), encoding='utf-8')
    if not recibo.exists():
        raise ErrorVision('Checkpoint existente sin procedencia registrada: no se deserializa ni sobrescribe.')
    datos_recibo = json.loads(recibo.read_text(encoding='utf-8'))
    if datos_recibo.get('url') != WEIGHTS_URL or datos_recibo.get('sha256') != sha256_archivo(checkpoint):
        raise ErrorVision('El checkpoint no coincide con su descarga aprobada.')

    import torch
    import torchxrayvision as xrv
    from safetensors.torch import save_file, load_file
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    # Solo en preparación: checkpoint oficial de confianza, nunca aportado por una solicitud.
    original = xrv.models.DenseNet(weights=MODEL_ID, cache_dir=str(carpeta)).cpu().eval()
    if list(original.pathologies) != list(TARGETS):
        raise ErrorVision('El mapa de etiquetas del peso no coincide con el esperado.')
    umbrales = original.op_threshs.detach().cpu().tolist()
    prueba = torch.zeros((1, 1, 224, 224), dtype=torch.float32)
    with torch.inference_mode():
        referencia = original(prueba).clone()
    destino = carpeta / WEIGHTS_FILE
    if destino.exists():
        raise ErrorVision('Ya hay una conversión sin manifest; revisa esos archivos antes de preparar de nuevo.')
    save_file({k: v.detach().cpu().contiguous() for k, v in original.state_dict().items()}, str(destino))
    del original
    gc.collect()
    local = xrv.models.DenseNet(weights=None, op_threshs=torch.tensor(umbrales)).cpu().eval()
    local.load_state_dict(load_file(str(destino), device='cpu'), strict=True)
    with torch.inference_mode():
        conversion = local(prueba)
    error = float((referencia - conversion).abs().max())
    if not torch.allclose(referencia, conversion, rtol=1e-6, atol=1e-7):
        raise ErrorVision('La conversión local no conserva la salida del modelo oficial.')
    datos = {
        'schema_version': 1, 'model': MODEL_ID, 'xrv_version': XRV_VERSION,
        'torch_preparation_version': torch.__version__, 'targets': list(TARGETS),
        'op_threshs': umbrales, 'preprocessing': PREPROCESS_VERSION, 'score_kind': SCORE_KIND,
        'weights_sha256': sha256_archivo(destino), 'checkpoint_sha256': datos_recibo['sha256'],
        'checkpoint_url': WEIGHTS_URL, 'conversion_max_abs_error': error,
        'license_reference': 'https://github.com/mlmed/torchxrayvision/blob/main/LICENSE',
        'experimental': True, 'clinically_calibrated': False,
    }
    (carpeta / 'manifest.json').write_text(json.dumps(datos, indent=2), encoding='utf-8')
    return comprobar_artefactos(carpeta)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument('--descargar', action='store_true', help='Autoriza descarga SOLO en instalación/preparación')
    args = parser.parse_args()
    try:
        datos = preparar(args.model_dir, args.descargar)
    except (ErrorVision, OSError, ValueError) as error:
        raise SystemExit(str(error)) from None
    print(json.dumps({'model': datos['model'], 'weights_sha256': datos['weights_sha256'],
        'conversion_max_abs_error': datos['conversion_max_abs_error'], 'prepared': True}, indent=2))


if __name__ == '__main__':
    main()
