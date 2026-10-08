from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Examen:
    id: int | None
    paciente_id: int
    tipo: str
    estado: str = "pendiente_muestra"
