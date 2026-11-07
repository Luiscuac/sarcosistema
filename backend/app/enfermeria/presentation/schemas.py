from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AdmisionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    motivo_consulta: str | None = Field(default=None, max_length=5000)
    sintomas: str | None = Field(default=None, max_length=5000)
    observaciones_enfermeria: str | None = Field(default=None, max_length=5000)
    peso_kg: float | None = Field(default=None, gt=0, le=500)
    talla_cm: float | None = Field(default=None, gt=0, le=300)
    temperatura_c: float | None = Field(default=None, ge=25, le=45)
    frecuencia_cardiaca: float | None = Field(default=None, ge=1, le=300)
    frecuencia_respiratoria: float | None = Field(default=None, ge=1, le=100)
    presion_sistolica: float | None = Field(default=None, ge=1, le=300)
    presion_diastolica: float | None = Field(default=None, ge=1, le=200)
    saturacion_oxigeno: float | None = Field(default=None, ge=1, le=100)
    dolor_escala: int | None = Field(default=None, ge=0, le=10)

    @field_validator('motivo_consulta', 'sintomas', 'observaciones_enfermeria')
    @classmethod
    def limpiar_texto(cls, value):
        limpio = value.strip() if value else None
        return limpio or None

    @field_validator('peso_kg', 'talla_cm', 'temperatura_c', 'frecuencia_cardiaca',
                     'frecuencia_respiratoria', 'presion_sistolica',
                     'presion_diastolica', 'saturacion_oxigeno')
    @classmethod
    def finito(cls, value):
        if value is not None and not isfinite(value):
            raise ValueError('La medición debe ser finita.')
        return value

    @model_validator(mode='after')
    def requiere_dato(self):
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError('Registra al menos un dato de admisión o una medición.')
        if (self.presion_sistolica is not None and self.presion_diastolica is not None
                and self.presion_sistolica <= self.presion_diastolica):
            raise ValueError('La presión sistólica debe superar la diastólica.')
        return self
