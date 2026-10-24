from dataclasses import dataclass


@dataclass(slots=True)
class Usuario:
    id: int
    identificador_acceso: str
    rol: str
    activo: bool
    contrasena_hash: str | None = None
