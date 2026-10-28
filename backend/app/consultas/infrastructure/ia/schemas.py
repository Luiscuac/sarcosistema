"""El LLM selecciona citas literales; solo genera un valor para medidas numéricas."""
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt

from app.consultas.domain.extraccion import CampoClinico, NUMERICOS, SalidaModelo, Sugerencia


class Captura(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campo: CampoClinico
    evidencia: str = Field(min_length=1, max_length=3000)
    numero: StrictFloat | StrictInt | None = None
    ambiguo: bool = False


class CapturaModelo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campos: list[Captura] = Field(default_factory=list, max_length=24)
    multiples_pacientes: bool = False
    identidad_incierta: bool = False

    def propuestas(self) -> SalidaModelo:
        return SalidaModelo(campos=[
            Sugerencia(campo=c.campo, evidencia=c.evidencia,
                valor=c.numero if c.campo in NUMERICOS else c.evidencia, ambiguo=c.ambiguo)
            for c in self.campos if c.campo not in NUMERICOS or c.numero is not None
        ], multiples_pacientes=self.multiples_pacientes, identidad_incierta=self.identidad_incierta)
