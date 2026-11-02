from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class PacienteResumen:
    id: int
    codigo_paciente: str
    nombre_completo: str
    numero_documento: str | None
    fecha_nacimiento: date
    sexo: str
    historia_clinica: str | None = None
    codigo_externo: str | None = None


@dataclass(frozen=True, slots=True)
class PacienteNuevo:
    nombre_completo: str
    fecha_nacimiento: date
    sexo: str
    tipo_documento: str | None
    numero_documento: str | None
    sin_documento: bool
    historia_clinica: str | None = None
    codigo_externo: str | None = None
