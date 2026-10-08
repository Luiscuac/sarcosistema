from typing import Protocol


class PasswordVerifier(Protocol):
    def verificar(self, password: str, hash_guardado: str) -> bool: ...
