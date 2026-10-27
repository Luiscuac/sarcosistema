from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EstudioCatalogo:
    id: int
    codigo: str
    nombre: str
    requiere_muestra: bool
    requiere_informe: bool
    plantilla_configurada: bool
    categoria_laboratorio: str | None = None


@dataclass(frozen=True, slots=True)
class EstudioPendiente:
    estudio_id: int
    referencia_estudio: str
    solicitud_id: int
    referencia_solicitud: str
    paciente_id: int
    paciente_nombre: str
    tipo_estudio_id: int
    tipo_estudio_nombre: str
    prioridad: str
    estado: str
    fecha_solicitud: datetime
    plantilla_configurada: bool = False
    categoria_laboratorio: str | None = None
