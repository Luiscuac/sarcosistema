"""Contrato JSON que Ollama debe respetar (salida estructurada).

El modelo devuelve solo los campos mencionados, cada uno con el valor redactado y
la cita literal que lo respalda. Todos los valores llegan como texto; los signos
vitales se convierten a número al validarlos en el dominio.
"""
from pydantic import BaseModel, ConfigDict, Field

from app.consultas.domain.extraccion import CampoClinico, SalidaModelo, Sugerencia


class Captura(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campo: CampoClinico
    valor: str = Field(min_length=1, max_length=3000)
    evidencia: str = Field(min_length=1, max_length=3000)
    ambiguo: bool = False


class CapturaModelo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campos: list[Captura] = Field(default_factory=list, max_length=25)
    multiples_pacientes: bool = False
    identidad_incierta: bool = False

    def propuestas(self) -> SalidaModelo:
        return SalidaModelo(
            campos=[Sugerencia(campo=c.campo, valor=c.valor, evidencia=c.evidencia, ambiguo=c.ambiguo) for c in self.campos],
            multiples_pacientes=self.multiples_pacientes,
            identidad_incierta=self.identidad_incierta,
        )
