from dataclasses import dataclass


@dataclass(frozen=True)
class RegistroPrueba:
    id: str
    codigo: str
    nombre: str
    fecha: str
    tipo_examen: str
    resultado: str
    unidad: str

