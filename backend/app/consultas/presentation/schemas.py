from uuid import UUID
from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.consultas.domain.extraccion import CampoClinico


NARRATIVAS = (
    'sintomas', 'enfermedad_actual', 'antecedentes', 'examen_fisico', 'hallazgos',
    'observaciones', 'evaluacion_clinica', 'diagnosticos_secundarios', 'tratamiento',
    'medicamentos', 'indicaciones', 'estudios_solicitados', 'referencias',
    'recomendaciones', 'plan_seguimiento',
)
MEDICIONES = (
    'peso_kg', 'talla_cm', 'temperatura_c', 'frecuencia_cardiaca',
    'frecuencia_respiratoria', 'presion_sistolica', 'presion_diastolica',
    'saturacion_oxigeno',
)


class RevisionIA(BaseModel):
    model_config = ConfigDict(extra='forbid')
    propuesta_id: UUID
    modelo: str = Field(min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_.:/-]+$')
    campos_aceptados: list[CampoClinico] = Field(max_length=24)


class ExtraerDatosRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    paciente_id: int = Field(gt=0)
    transcripcion: str = Field(min_length=2, max_length=12000)

    @field_validator('transcripcion')
    @classmethod
    def no_vacia(cls, value):
        if len(value.strip()) < 2:
            raise ValueError('La transcripción está vacía.')
        return value


class ConsultaNueva(BaseModel):
    model_config = ConfigDict(extra='forbid')
    paciente_id: int = Field(gt=0)
    clave_idempotencia: UUID
    revision_ia: RevisionIA | list[RevisionIA] | None = None
    motivo_consulta: str = Field(min_length=1, max_length=5000)
    diagnostico_principal: str = Field(min_length=1, max_length=5000)
    sintomas: str | None = None
    enfermedad_actual: str | None = None
    antecedentes: str | None = None
    examen_fisico: str | None = None
    hallazgos: str | None = None
    observaciones: str | None = None
    evaluacion_clinica: str | None = None
    diagnosticos_secundarios: str | None = None
    tratamiento: str | None = None
    medicamentos: str | None = None
    indicaciones: str | None = None
    estudios_solicitados: str | None = None
    referencias: str | None = None
    recomendaciones: str | None = None
    plan_seguimiento: str | None = None
    peso_kg: float | None = None
    talla_cm: float | None = None
    temperatura_c: float | None = None
    frecuencia_cardiaca: float | None = None
    frecuencia_respiratoria: float | None = None
    presion_sistolica: float | None = None
    presion_diastolica: float | None = None
    saturacion_oxigeno: float | None = None

    @field_validator('motivo_consulta', 'diagnostico_principal', *NARRATIVAS)
    @classmethod
    def limpiar_texto(cls, value):
        if value is None:
            return None
        limpio = value.strip()
        if len(limpio) > 10000:
            raise ValueError('El texto excede el máximo de 10000 caracteres.')
        return limpio or None

    @field_validator(*MEDICIONES)
    @classmethod
    def medicion_positiva(cls, value):
        if value is not None and (not isfinite(value) or value <= 0):
            raise ValueError('La medición debe ser positiva y finita.')
        return value

    @model_validator(mode='after')
    def validar(self):
        if isinstance(self.revision_ia, list) and len(self.revision_ia) > 50:
            raise ValueError('Demasiadas revisiones IA en una consulta.')
        if not self.motivo_consulta or not self.diagnostico_principal:
            raise ValueError('Motivo de consulta y diagnóstico principal son obligatorios.')
        if self.saturacion_oxigeno is not None and self.saturacion_oxigeno > 100:
            raise ValueError('La saturación no puede superar el 100 %.')
        if self.presion_sistolica is not None and self.presion_diastolica is not None and self.presion_sistolica <= self.presion_diastolica:
            raise ValueError('La presión sistólica debe superar la diastólica.')
        return self

    def contenido(self):
        return self.model_dump(exclude={'paciente_id', 'clave_idempotencia', 'motivo_consulta', 'revision_ia'}, mode='json')
