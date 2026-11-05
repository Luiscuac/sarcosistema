"""Contratos de visión experimental, separados de diagnósticos confirmados."""
from dataclasses import dataclass
from pathlib import Path

MODEL_ID = 'densenet121-res224-all'
XRV_VERSION = '1.5.7'
WEIGHTS_FILE = 'densenet121-res224-all.safetensors'
PREPROCESS_VERSION = 'xrv-normalize255-mean-center-resize224-v1'
SCORE_KIND = 'sigmoid_with_xrv_operating_point_normalization'
TARGETS = (
    'Atelectasis', 'Consolidation', 'Infiltration', 'Pneumothorax', 'Edema',
    'Emphysema', 'Fibrosis', 'Effusion', 'Pneumonia', 'Pleural_Thickening',
    'Cardiomegaly', 'Nodule', 'Mass', 'Hernia', 'Lung Lesion', 'Fracture',
    'Lung Opacity', 'Enlarged Cardiomediastinum',
)
SELECTED_TARGETS = ('Consolidation', 'Effusion', 'Cardiomegaly')
MAX_IMAGE_BYTES = 10 * 1024**2


class ErrorVision(Exception):
    pass


class ModeloNoPreparado(ErrorVision):
    pass


class ImagenNoValida(ErrorVision):
    pass


class RecursosInsuficientes(ErrorVision):
    pass


class InferenciaOcupada(ErrorVision):
    pass


class TiempoAgotado(ErrorVision):
    pass


@dataclass(frozen=True)
class VisionConfig:
    model_dir: Path
    min_free_bytes: int = 4 * 1024**3
    threads: int = 4
    timeout_seconds: float = 120

    def __post_init__(self):
        if not 1 <= self.threads <= 4 or not 1 <= self.timeout_seconds <= 600 or self.min_free_bytes < 512 * 1024**2:
            raise ValueError('Configuración de recursos de visión no válida.')
