from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CampoRellenoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector_tipo: Literal["automation_id", "nombre", "indice"]
    selector: str = Field(min_length=1, max_length=256)
    valor: str = Field(max_length=10000)


class SolicitudRellenoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campos: list[CampoRellenoRequest] = Field(min_length=1, max_length=100)


class SolicitudTransporteDemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paciente_nombre: str = Field(min_length=1, max_length=300)
    codigo_paciente: str = Field(min_length=1, max_length=100)
    historia_clinica: str | None = Field(default=None, max_length=100)
    profesional: str = Field(min_length=1, max_length=300)
    datos: dict[str, str | float | None] = Field(max_length=30)
