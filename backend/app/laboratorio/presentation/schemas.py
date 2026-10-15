"""
DTOs (Pydantic) del modulo laboratorio.
Equivalente a crear-examen.dto.ts: que forma deben tener los datos de entrada/salida.
"""
from pydantic import BaseModel, Field


class CrearExamenDTO(BaseModel):
    paciente_id: int = Field(..., gt=0)
    tipo: str = Field(..., min_length=1, max_length=100)


class ExamenOut(BaseModel):
    id: int
    paciente_id: int
    tipo: str
    estado: str

    model_config = {"from_attributes": True}
