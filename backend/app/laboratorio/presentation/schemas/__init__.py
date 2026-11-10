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
    telefono: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def validar_documento(self):
        self.tipo_documento = (self.tipo_documento or "").strip() or None
        self.numero_documento = (self.numero_documento or "").strip() or None
        if not self.sin_documento and not (self.tipo_documento and self.numero_documento):
            raise ValueError("Ingresa el documento o marca que la persona no tiene documento")
        if self.sin_documento and self.numero_documento:
            raise ValueError("Una persona marcada sin documento no puede tener número de documento")
        if self.fecha_nacimiento > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        self.nombre_completo = self.nombre_completo.strip()
        if len(self.nombre_completo) < 2:
            raise ValueError("El nombre debe tener al menos dos caracteres")
        self.historia_clinica = self.historia_clinica.strip() if self.historia_clinica else None
        self.codigo_externo = self.codigo_externo.strip() if self.codigo_externo else None
        self.historia_clinica = self.historia_clinica or None
        self.codigo_externo = self.codigo_externo or None
        self.telefono = self.telefono.strip() or None if self.telefono else None
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
    telefono: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PacienteCreadoResponse(PacienteResponse):
    pass


class MedicoSolicitanteResponse(BaseModel):
    id: int
    nombre: str


class CrearSolicitudRequest(BaseModel):
    paciente_id: int = Field(gt=0)
    tipo_estudio_ids: list[int] = Field(min_length=1, max_length=30)
    fecha_solicitud: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    referencia_papel_formulario: str | None = Field(default=None, max_length=100)
    establecimiento_solicitante_nombre: str | None = Field(default=None, max_length=200)
    procedencia: Literal["este_centro", "otro_centro"] = "este_centro"
    medico_solicitante_nombre: str = Field(min_length=2, max_length=200)
    medico_solicitante_id: int | None = Field(default=None, gt=0)
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
        self.establecimiento_solicitante_nombre = (
            self.establecimiento_solicitante_nombre.strip()
            if self.establecimiento_solicitante_nombre else None
        )
        if self.procedencia == "otro_centro" and not self.establecimiento_solicitante_nombre:
            raise ValueError("Indica el nombre del otro centro")
        if self.procedencia == "este_centro":
            self.establecimiento_solicitante_nombre = None
            if self.medico_solicitante_id is None:
                raise ValueError("Selecciona un médico registrado de Sarcobamba")
        elif self.medico_solicitante_id is not None:
            raise ValueError("Para otro centro escribe el nombre del profesional")
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


class EstudioDetalleResponse(BaseModel):
    estudio_id: int
    referencia_estudio: str
    tipo_estudio_nombre: str
    categoria_laboratorio: str | None
    estado: str
    tipo_estudio_codigo: str | None = None
    incidencias: list["IncidenciaResponse"] = Field(default_factory=list)


class IncidenciaResponse(BaseModel):
    motivo: str
    descripcion: str
    responsable: str
    fecha_hora: datetime


class MuestraDetalleResponse(BaseModel):
    referencia: str
    tipo_muestra: str | None
    fecha_toma: date
    responsable_recepcion: str | None
    estudio_ids: list[int]


class RegistrarIncidenciaRequest(BaseModel):
    motivo: Literal["muestra_no_entregada", "toma_rechazada", "toma_no_realizada"]
    descripcion: str = Field(min_length=3, max_length=1000)
    responsable: str = Field(min_length=2, max_length=200)

    @model_validator(mode="after")
    def limpiar_textos(self):
        self.descripcion = self.descripcion.strip()
        self.responsable = self.responsable.strip()
        if len(self.descripcion) < 3 or len(self.responsable) < 2:
            raise ValueError("Indica el motivo y el responsable de la incidencia")
        return self


class RegistrarIncidenciasSolicitudRequest(RegistrarIncidenciaRequest):
    estudio_ids: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_estudios(self):
        if any(estudio_id <= 0 for estudio_id in self.estudio_ids):
            raise ValueError("Cada estudio debe tener un identificador válido")
        if len(self.estudio_ids) != len(set(self.estudio_ids)):
            raise ValueError("No repitas estudios en una incidencia")
        return self


class IncidenciasRegistradasResponse(BaseModel):
    cantidad: int


class SolicitudDetalleResponse(BaseModel):
    id: int
    referencia: str
    paciente_nombre: str
    paciente_documento: str | None
    fecha_solicitud: datetime
    fecha_registro: datetime | None
    referencia_papel_formulario: str | None
    procedencia: str
    establecimiento_solicitante_nombre: str | None
    medico_solicitante_nombre: str | None
    diagnostico_principal: str | None
    prioridad: str
    estudios: list[EstudioDetalleResponse]
    muestras: list[MuestraDetalleResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ParametroInformeResponse(BaseModel):
    nombre: str
    seccion: str | None
    valor: str
    unidad: str | None
    rango_referencia: str | None


class ResultadoInformeResponse(BaseModel):
    nombre: str
    categoria: str | None
    referencia: str
    parametros: list[ParametroInformeResponse]
    observaciones: str | None
    responsable_publicacion: str | None


class EstudioNoRealizadoInformeResponse(BaseModel):
    nombre: str
    categoria: str | None
    referencia: str
    motivo: str
    descripcion: str
    responsable: str
    fecha_hora: datetime


class InformeSolicitudResponse(BaseModel):
    referencia: str
    paciente_nombre: str
    paciente_documento: str | None
    fecha_solicitud: datetime
    referencia_papel_formulario: str | None
    procedencia: str
    establecimiento_solicitante_nombre: str | None
    medico_solicitante_nombre: str | None
    resultados: list[ResultadoInformeResponse]
    estudios_no_realizados: list[EstudioNoRealizadoInformeResponse] = Field(default_factory=list)


class RecibirMuestraRequest(BaseModel):
    tipo_muestra: str = Field(min_length=1, max_length=120)
    fecha_toma: date
    hora_toma: time | None = None
    hora_no_registrada: bool = False
    responsable_recepcion: str = Field(min_length=2, max_length=200)

    @model_validator(mode="after")
    def validar_hora(self):
        self.tipo_muestra = self.tipo_muestra.strip()
        if not self.tipo_muestra:
            raise ValueError("Indica el tipo de muestra recibido")
        if self.hora_no_registrada == (self.hora_toma is not None):
            raise ValueError("Registra una hora o marca que no fue registrada")
        self.responsable_recepcion = self.responsable_recepcion.strip()
        if len(self.responsable_recepcion) < 2:
            raise ValueError("Indica quién tomó o recibió la muestra")
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
    opciones: list[str] = Field(default_factory=list)


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
    responsable_analisis: str | None = None
    responsable_publicacion: str | None = None
    parametros: list[ParametroResultadoResponse]


class ValorResultadoRequest(BaseModel):
    parametro_id: int = Field(gt=0)
    valor: str | None = Field(default=None, max_length=2000)


class GuardarBorradorRequest(BaseModel):
    valores: list[ValorResultadoRequest]
    observaciones: str | None = Field(default=None, max_length=4000)
    responsable_analisis: str = Field(min_length=2, max_length=200)

    @model_validator(mode="after")
    def parametros_unicos(self):
        ids = [item.parametro_id for item in self.valores]
        if len(ids) != len(set(ids)):
            raise ValueError("No repitas parámetros en el resultado")
        self.responsable_analisis = self.responsable_analisis.strip()
        if len(self.responsable_analisis) < 2:
            raise ValueError("Indica el profesional responsable del resultado")
        return self


class PublicarResultadoRequest(BaseModel):
    responsable_publicacion: str = Field(min_length=2, max_length=200)

    @model_validator(mode="after")
    def validar_responsable(self):
        self.responsable_publicacion = self.responsable_publicacion.strip()
        if len(self.responsable_publicacion) < 2:
            raise ValueError("Indica quién revisó y autorizó el informe")
        return self


class EstudioBorradorAreaRequest(BaseModel):
    estudio_id: int = Field(gt=0)
    valores: list[ValorResultadoRequest]


class GuardarBorradorAreaRequest(BaseModel):
    estudios: list[EstudioBorradorAreaRequest] = Field(min_length=1)
    observaciones: str | None = Field(default=None, max_length=4000)
    responsable: str = Field(min_length=2, max_length=200)

    @model_validator(mode="after")
    def validar_area(self):
        ids = [estudio.estudio_id for estudio in self.estudios]
        if len(ids) != len(set(ids)):
            raise ValueError("No repitas estudios en el borrador del área")
        self.responsable = self.responsable.strip()
        if len(self.responsable) < 2:
            raise ValueError("Indica el profesional responsable del área")
        return self


class PublicarResultadosAreaRequest(BaseModel):
    estudio_ids: list[int] = Field(min_length=1)
    responsable: str = Field(min_length=2, max_length=200)

    @model_validator(mode="after")
    def validar_area(self):
        if any(estudio_id <= 0 for estudio_id in self.estudio_ids):
            raise ValueError("Cada estudio debe tener un identificador válido")
        if len(self.estudio_ids) != len(set(self.estudio_ids)):
            raise ValueError("No repitas estudios al publicar el área")
        self.responsable = self.responsable.strip()
        if len(self.responsable) < 2:
            raise ValueError("Indica el profesional responsable del área")
        return self


class ResultadoAreaAccionResponse(BaseModel):
    cantidad: int = Field(ge=1)
    estado: Literal["borrador", "publicado"]


class ResultadoAccionResponse(BaseModel):
    estudio_id: int
    estado: str
    numero_version: int


class MuestraRecibidaResponse(BaseModel):
    referencia_muestra: str
