from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True, slots=True)
class TomaMuestraNueva:
    estudio_id: int
    tipo_muestra: str
    fecha_toma: date
    hora_toma: time | None
    hora_no_registrada: bool


@dataclass(frozen=True, slots=True)
class MuestraSolicitudNueva:
    solicitud_id: int
    estudio_ids: tuple[int, ...]
    tipo_muestra: str
    fecha_toma: date
    hora_toma: time | None
    hora_no_registrada: bool
