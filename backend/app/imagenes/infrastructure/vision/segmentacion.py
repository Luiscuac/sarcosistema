"""Máscara de campos pulmonares (PSPNet ChestX-Det de TorchXRayVision), opcional.

Solo safetensors local verificado contra su manifiesto; nunca descarga ni carga pickle.
Si no está preparada, `cargar_segmentador` devuelve None y los mapas funcionan como antes.
"""
import json
from pathlib import Path

DIRECTORIO = Path(__file__).resolve().parents[4] / '.models' / 'radiologia-segmentacion'
MANIFIESTO = 'manifest.json'
PESOS = 'pspnet-chestx-det.safetensors'
ESTRUCTURAS = ('Left Clavicle', 'Right Clavicle', 'Left Scapula', 'Right Scapula', 'Left Lung', 'Right Lung',
               'Left Hilus Pulmonis', 'Right Hilus Pulmonis', 'Heart', 'Aorta', 'Facies Diaphragmatica',
               'Mediastinum', 'Weasand', 'Spine')
PULMONES = (ESTRUCTURAS.index('Left Lung'), ESTRUCTURAS.index('Right Lung'))


def construir_modelo():
    from torchxrayvision.baseline_models.chestx_det import pspnet
    return pspnet(len(ESTRUCTURAS)).cpu().eval()


def segmentacion_preparada(directorio: Path = DIRECTORIO) -> bool:
    return (directorio / MANIFIESTO).is_file() and (directorio / PESOS).is_file()


def cargar_segmentador(directorio: Path = DIRECTORIO):
    if not segmentacion_preparada(directorio):
        return None
    from app.imagenes.domain.vision import ErrorVision
    from app.imagenes.infrastructure.vision.artefactos import sha256_archivo
    from safetensors.torch import load_file
    manifiesto = json.loads((directorio / MANIFIESTO).read_text(encoding='utf-8'))
    if manifiesto.get('targets') != list(ESTRUCTURAS) or sha256_archivo(directorio / PESOS) != manifiesto.get('weights_sha256'):
        raise ErrorVision('La segmentación pulmonar local no supera la verificación de integridad.')
    modelo = construir_modelo()
    modelo.load_state_dict(load_file(str(directorio / PESOS), device='cpu'), strict=True)
    return modelo


def mascara_pulmonar(segmentador, tensor, dilatacion: int = 7):
    """tensor XRV [1,1,224,224] en [-1024,1024] -> máscara float 224x224 (pulmones, dilatada)."""
    import torch
    import torch.nn.functional as F
    import torchvision
    with torch.inference_mode():
        x = F.interpolate(tensor.repeat(1, 3, 1, 1), size=(512, 512), mode='bilinear', align_corners=False)
        x = torchvision.transforms.functional.normalize((x + 1024) / 2048, [0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        logits = segmentador(x)
        pulmones = (torch.sigmoid(logits[:, list(PULMONES)]) > 0.5).any(dim=1, keepdim=True).float()
        mascara = F.interpolate(pulmones, size=tensor.shape[-2:], mode='nearest')
        if dilatacion > 0:
            mascara = F.max_pool2d(mascara, kernel_size=2 * dilatacion + 1, stride=1, padding=dilatacion)
    return mascara[0, 0].numpy()
