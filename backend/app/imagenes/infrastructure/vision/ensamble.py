"""Ensamble opcional de 6 DenseNet XRV especialistas para el patrón de TB (no para el índice ni las 18 categorías).

Medido 2026-11-20 (docs/imagenes/2026-11-20-deteccion-tb.md): promediar el modelo base con nih, pc, chex, rsna,
mimic_nb y mimic_ch mejora el patrón TB en hospitales externos; el índice empeora, por eso solo se usa aquí.
Solo safetensors locales verificados contra su manifiesto; nunca descarga ni carga pickle.
Si no está preparado, el patrón TB usa el artefacto v1 (solo modelo base).
"""
import json
import math
from pathlib import Path

DIRECTORIO = Path(__file__).resolve().parents[4] / '.models' / 'radiologia-ensamble'
MANIFIESTO = 'manifest.json'
MODELOS = ('nih', 'pc', 'chex', 'rsna', 'mimic_nb', 'mimic_ch')


def ensamble_preparado(directorio: Path = DIRECTORIO) -> bool:
    if not (directorio / MANIFIESTO).is_file():
        return False
    try:
        datos = json.loads((directorio / MANIFIESTO).read_text(encoding='utf-8'))
        return all((directorio / datos['modelos'][n]['weights_file']).is_file() for n in MODELOS)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def promediar(base: dict, especialistas: list[dict]) -> dict:
    """Promedio por categoría del modelo base y de los especialistas entrenados en ella. Puro: sin torch."""
    salida = {}
    for nombre, valor in base.items():
        valores = [valor] + [e[nombre] for e in especialistas
                             if nombre in e and isinstance(e[nombre], (int, float)) and math.isfinite(e[nombre])]
        salida[nombre] = sum(valores) / len(valores)
    return salida


def puntuaciones_especialistas(tensor, directorio: Path = DIRECTORIO) -> list[dict]:
    """Carga cada especialista de a uno (pico de RAM ≈ un modelo), infiere y lo libera."""
    import gc
    import torch
    import torchxrayvision as xrv
    from safetensors.torch import load_file
    from app.imagenes.domain.vision import ErrorVision
    from app.imagenes.infrastructure.vision.artefactos import sha256_archivo
    manifiesto = json.loads((directorio / MANIFIESTO).read_text(encoding='utf-8'))
    resultados = []
    for nombre in MODELOS:
        meta = manifiesto['modelos'][nombre]
        pesos = directorio / meta['weights_file']
        if sha256_archivo(pesos) != meta['weights_sha256']:
            raise ErrorVision('Un modelo del ensamble local no supera la verificación de integridad.')
        umbrales = torch.tensor([math.nan if u is None else u for u in meta['op_threshs']])
        modelo = xrv.models.DenseNet(weights=None, op_threshs=umbrales).cpu().eval()
        modelo.load_state_dict(load_file(str(pesos), device='cpu'), strict=True)
        with torch.inference_mode():
            valores = modelo(tensor)[0].tolist()
        resultados.append({t: v for t, v, u in zip(meta['targets'], valores, meta['op_threshs'])
                           if t and u is not None and math.isfinite(v)})
        del modelo
        gc.collect()
    return resultados
