from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SolicitudNueva:
    paciente_id: int
    tipo_estudio_ids: tuple[int, ...]
    fecha_solicitud: datetime
    referencia_papel_formulario: str | None
    establecimiento_solicitante_nombre: str | None
    medico_solicitante_nombre: str
    diagnostico_principal: str | None
    prioridad: str
    clave_idempotencia: str


@dataclass(frozen=True, slots=True)
class EstudioSolicitadoResumen:
    id: int
    referencia: str
    tipo_estudio_id: int
    tipo_estudio_nombre: str
    estado: str


@dataclass(frozen=True, slots=True)
class SolicitudCreada:
    id: int
    referencia: str
    paciente_id: int
    paciente_nombre: str
    fecha_solicitud: datetime
    prioridad: str
    estudios: tuple[EstudioSolicitadoResumen, ...]
