from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    id: int
    identificador_acceso: str
    rol: str
