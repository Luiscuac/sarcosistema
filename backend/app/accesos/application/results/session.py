from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Sesion:
    access_token: str
    token_type: str = "bearer"
