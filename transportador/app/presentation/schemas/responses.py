from pydantic import BaseModel


class VentanaResponse(BaseModel):
    handle: int
    titulo: str
    proceso_id: int


class CampoEditableResponse(BaseModel):
    automation_id: str
    nombre: str
    tipo: str
    habilitado: bool
    selector_tipo: str
    selector: str
    indice: int
    configurable: bool
