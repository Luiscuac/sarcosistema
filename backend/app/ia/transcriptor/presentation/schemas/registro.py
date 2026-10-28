from pydantic import BaseModel


class RegistroPruebaResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    fecha: str
    tipo_examen: str
    resultado: str
    unidad: str

