"""Adaptador Argon2 para creación y verificación de hashes de contraseña."""
from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerificationError


class Argon2PasswordHasher:
    def __init__(self):
        self._hasher = Argon2Hasher()

    def hashear(self, password: str) -> str:
        return self._hasher.hash(password)

    def verificar(self, password: str, hash_guardado: str) -> bool:
        try:
            return self._hasher.verify(hash_guardado, password)
        except (InvalidHashError, VerificationError):
            return False
