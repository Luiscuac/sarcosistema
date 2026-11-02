from datetime import date, datetime, time, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EstudioCatalogoResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    requiere_muestra: bool
    requiere_informe: bool
    plantilla_configurada: bool
    categoria_laboratorio: str | None = None

    model_config = ConfigDict(from_attributes=True)


class EstudioPendienteResponse(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)


class CrearPacienteRequest(BaseModel):
    nombre_completo: str = Field(min_length=2, max_length=200)
    fecha_nacimiento: date
    sexo: Literal["M", "F", "otro", "no_especificado"]
    tipo_documento: str | None = Field(default=None, max_length=40)
    numero_documento: str | None = Field(default=None, max_length=80)
    sin_documento: bool = False
    historia_clinica: str | None = Field(default=None, max_length=80)
    codigo_externo: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validar_documento(self):
        if not self.sin_documento and not (self.tipo_documento and self.numero_documento):
            raise ValueError("Ingresa el documento o marca que la persona no tiene documento")
        if self.sin_documento and self.numero_documento:
            raise ValueError("Una persona marcada sin documento no puede tener número de documento")
        self.nombre_completo = self.nombre_completo.strip()
        if len(self.nombre_completo) < 2:
            raise ValueError("El nombre debe tener al menos dos caracteres")
        self.historia_clinica = self.historia_clinica.strip() if self.historia_clinica else None
        self.codigo_externo = self.codigo_externo.strip() if self.codigo_externo else None
        self.historia_clinica = self.historia_clinica or None
        self.codigo_externo = self.codigo_externo or None
        return self


class PacienteResponse(BaseModel):
    id: int
    codigo_paciente: str
    nombre_completo: str
    numero_documento: str | None
    fecha_nacimiento: date
    sexo: str
    historia_clinica: str | None = None
    codigo_externo: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PacienteCreadoResponse(PacienteResponse):
    pass


class CrearSolicitudRequest(BaseModel):
    paciente_id: int = Field(gt=0)
    tipo_estudio_ids: list[int] = Field(min_length=1, max_length=30)
    fecha_solicitud: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    referencia_papel_formulario: str | None = Field(default=None, max_length=100)
    establecimiento_solicitante_nombre: str | None = Field(default=None, max_length=200)
    medico_solicitante_nombre: str = Field(min_length=2, max_length=200)
    diagnostico_principal: str | None = Field(default=None, max_length=500)
    prioridad: Literal["urgente", "sin_prioridad"] = "sin_prioridad"
    clave_idempotencia: UUID

    @model_validator(mode="after")
    def validar_solicitud(self):
        if any(tipo_id <= 0 for tipo_id in self.tipo_estudio_ids):
            raise ValueError("Cada estudio debe tener un identificador válido")
        if len(self.tipo_estudio_ids) != len(set(self.tipo_estudio_ids)):
            raise ValueError("No repitas el mismo estudio en una solicitud")
        self.medico_solicitante_nombre = self.medico_solicitante_nombre.strip()
        if len(self.medico_solicitante_nombre) < 2:
            raise ValueError("Registra el nombre del profesional solicitante")
        return self


class EstudioSolicitadoResponse(BaseModel):
    id: int
    referencia: str
    tipo_estudio_id: int
    tipo_estudio_nombre: str
    estado: str

    model_config = ConfigDict(from_attributes=True)


class SolicitudCreadaResponse(BaseModel):
    id: int
    referencia: str
    paciente_id: int
    paciente_nombre: str
    fecha_solicitud: datetime
    prioridad: str
    estudios: list[EstudioSolicitadoResponse]

    model_config = ConfigDict(from_attributes=True)


class RecibirMuestraRequest(BaseModel):
    tipo_muestra: str = Field(min_length=1, max_length=120)
    fecha_toma: date
    hora_toma: time | None = None
    hora_no_registrada: bool = False

    @model_validator(mode="after")
    def validar_hora(self):
        self.tipo_muestra = self.tipo_muestra.strip()
        if not self.tipo_muestra:
            raise ValueError("Indica el tipo de muestra recibido")
        if self.hora_no_registrada == (self.hora_toma is not None):
            raise ValueError("Registra una hora o marca que no fue registrada")
        return self


class RecibirMuestraSolicitudRequest(RecibirMuestraRequest):
    estudio_ids: list[int] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def validar_estudios(self):
        if any(estudio_id <= 0 for estudio_id in self.estudio_ids):
            raise ValueError("Selecciona estudios válidos")
        if len(self.estudio_ids) != len(set(self.estudio_ids)):
            raise ValueError("No repitas estudios para una misma muestra")
        return self


class ParametroResultadoResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    tipo_entrada: str
    unidad: str | None
    rango_referencia: str | None
    obligatorio: bool
    orden: int
    seccion: str | None
    valor: str | None


class ResultadoEstudioResponse(BaseModel):
    estudio_id: int
    referencia_estudio: str
    paciente_nombre: str
    tipo_estudio_nombre: str
    estado_estudio: str
    estado_resultado: str | None
    numero_version: int | None
    plantilla_configurada: bool
    observaciones: str | None
    parametros: list[ParametroResultadoResponse]


class ValorResultadoRequest(BaseModel):
    parametro_id: int = Field(gt=0)
    valor: str | None = Field(default=None, max_length=2000)


class GuardarBorradorRequest(BaseModel):
    valores: list[ValorResultadoRequest]
    observaciones: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def parametros_unicos(self):
        ids = [item.parametro_id for item in self.valores]
        if len(ids) != len(set(ids)):
            raise ValueError("No repitas parámetros en el resultado")
        return self


class ResultadoAccionResponse(BaseModel):
    estudio_id: int
    estado: str
    numero_version: int


class MuestraRecibidaResponse(BaseModel):
    referencia_muestra: str
