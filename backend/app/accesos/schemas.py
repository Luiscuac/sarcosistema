"""
DTOs (Pydantic) del modulo accesos.
Entrada y salida del endpoint de login.
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    identificador_acceso: str = Field(..., min_length=1, max_length=200)
    contrasena: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre_usuario: str
