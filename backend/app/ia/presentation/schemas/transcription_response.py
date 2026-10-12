from pydantic import BaseModel


class TranscripcionResponse(BaseModel):
    texto: str
    requiere_revision: bool = True
