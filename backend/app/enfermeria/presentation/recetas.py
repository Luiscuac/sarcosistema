from datetime import date
from math import isfinite
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Medicamento(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre_generico: str = Field(min_length=1, max_length=300)
    forma_concentracion: str = Field(min_length=1, max_length=300)
    indicaciones: str = Field(min_length=1, max_length=2000)
    cantidad_recetada: str | None = Field(default=None, max_length=100)
    cantidad_dispensada: str | None = Field(default=None, max_length=100)
    valor_unitario: float | None = Field(default=None, ge=0)
    valor_total: float | None = Field(default=None, ge=0)


class RecetaRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    establecimiento: str | None = Field(default=None, max_length=200)
    programas: str | None = Field(default=None, max_length=1000)
    numero_receta: str | None = Field(default=None, max_length=100)
    venta: bool = False
    historia_clinica: str | None = Field(default=None, max_length=100)
    tipo_atencion: str | None = None
    fecha: date = Field(default_factory=date.today)
    diagnostico_principal: str | None = Field(default=None, max_length=1000)
    diagnostico_secundario: str | None = Field(default=None, max_length=1000)
    prestaciones: list[str] = Field(default_factory=list, max_length=50)
    medicamentos: list[Medicamento] = Field(min_length=1, max_length=30)
    dispensador: str | None = Field(default=None, max_length=200)
    prescriptor: str | None = Field(default=None, max_length=200)
    costo_total: float | None = Field(default=None, ge=0)
    paciente_firma: str | None = Field(default=None, max_length=200)

    @field_validator('tipo_atencion')
    @classmethod
    def tipo_valido(cls, value):
        if value is not None and value not in {'consultorio', 'domiciliaria', 'referencia'}:
            raise ValueError('Tipo de atención no válido.')
        return value

    @field_validator('establecimiento', 'programas', 'numero_receta', 'historia_clinica',
                     'diagnostico_principal', 'diagnostico_secundario', 'dispensador', 'prescriptor', 'paciente_firma')
    @classmethod
    def limpiar(cls, value):
        return value.strip() or None if value else None

    @field_validator('prestaciones')
    @classmethod
    def prestaciones_limpias(cls, values):
        return list(dict.fromkeys(v.strip() for v in values if v.strip()))
