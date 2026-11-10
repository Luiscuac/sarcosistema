from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True, slots=True)
class TomaMuestraNueva:
    estudio_id: int
    tipo_muestra: str
    fecha_toma: date
    hora_toma: time | None
    hora_no_registrada: bool
    responsable_recepcion: str = ""


@dataclass(frozen=True, slots=True)
class MuestraSolicitudNueva:
    solicitud_id: int
    estudio_ids: tuple[int, ...]
    tipo_muestra: str
    fecha_toma: date
    hora_toma: time | None
    hora_no_registrada: bool
    responsable_recepcion: str = ""


@dataclass(frozen=True, slots=True)
class IncidenciaNueva:
    estudio_id: int
    motivo: str
    descripcion: str
    responsable: str


@dataclass(frozen=True, slots=True)
class IncidenciaSolicitudNueva:
    solicitud_id: int
    estudio_ids: tuple[int, ...]
    motivo: str
    descripcion: str
    responsable: str
