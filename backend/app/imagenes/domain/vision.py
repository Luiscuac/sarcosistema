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
NOMBRES_ES = {
    'Atelectasis': 'atelectasia', 'Consolidation': 'consolidación', 'Infiltration': 'infiltrado',
    'Pneumothorax': 'neumotórax', 'Edema': 'edema pulmonar', 'Emphysema': 'enfisema', 'Fibrosis': 'fibrosis',
    'Effusion': 'derrame pleural', 'Pneumonia': 'neumonía', 'Pleural_Thickening': 'engrosamiento pleural',
    'Cardiomegaly': 'cardiomegalia', 'Nodule': 'nódulo', 'Mass': 'masa', 'Hernia': 'hernia',
    'Lung Lesion': 'lesión pulmonar', 'Fracture': 'fractura', 'Lung Opacity': 'opacidad pulmonar',
    'Enlarged Cardiomediastinum': 'ensanchamiento cardiomediastínico',
}
# Alineado con la subida (IMAGENES_MAX_MB=15 / IMAGENES_DICOM_MAX_MB=100): PNG/JPEG de equipos
# reales superan los 10 MiB y el DICOM de tórax suele estar entre 5 y 60 MiB.
MAX_RASTER_BYTES = 30 * 1024**2
MAX_IMAGE_BYTES = 100 * 1024**2


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
    # Limitar mapas de calor a los pulmones si la segmentación local está preparada (mejora medida en TB).
    mascara_pulmonar: bool = True

    def __post_init__(self):
        if not 1 <= self.threads <= 4 or not 1 <= self.timeout_seconds <= 600 or self.min_free_bytes < 512 * 1024**2:
            raise ValueError('Configuración de recursos de visión no válida.')
