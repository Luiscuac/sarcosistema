from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum


class AccionAuditoria(StrEnum):
    """Acciones permitidas por el dominio de auditoría del esquema."""

    CREAR = "crear"
    MODIFICAR = "modificar"
    PUBLICAR = "publicar"


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


@dataclass(frozen=True, slots=True)
class ParametroResultado:
    id: int
    codigo: str
    nombre: str
    tipo_entrada: str
    unidad: str | None
    rango_referencia: str | None
    obligatorio: bool
    orden: int
    seccion: str | None
    valor: str | None = None


@dataclass(frozen=True, slots=True)
class ResultadoEstudio:
    estudio_id: int
    referencia_estudio: str
    paciente_nombre: str
    tipo_estudio_nombre: str
    estado_estudio: str
    estado_resultado: str | None
    numero_version: int | None
    plantilla_configurada: bool
    observaciones: str | None
    parametros: tuple[ParametroResultado, ...]


@dataclass(frozen=True, slots=True)
class ValorResultadoEntrada:
    parametro_id: int
    valor: str | None


@dataclass(frozen=True, slots=True)
class BorradorResultado:
    estudio_id: int
    estado: str
    numero_version: int
