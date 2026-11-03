from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalisisNuevo(BaseModel):
    confirmar_torax_frontal: Literal[True]
    proyeccion: Literal['PA','AP','frontal_no_especificada']
    clave: str = Field(min_length=1,max_length=100)


class RevisionNueva(BaseModel):
    version: int = Field(ge=0)
    decision: Literal['aceptada_como_propuesta','corregida','rechazada']
    motivo: str = Field(default='',max_length=2000)
    correccion: str | None = Field(default=None,max_length=4000)

    @model_validator(mode='after')
    def datos_obligatorios(self):
        if self.decision != 'aceptada_como_propuesta' and not self.motivo.strip():
            raise ValueError('Se requiere motivo para corregir o rechazar.')
        if self.decision == 'corregida' and not (self.correccion or '').strip():
            raise ValueError('Se requiere el texto de corrección.')
        return self
