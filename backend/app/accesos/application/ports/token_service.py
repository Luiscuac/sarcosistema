from typing import Protocol


class TokenService(Protocol):
    def emitir(self, usuario_id: str, rol: str) -> str: ...

    def obtener_sujeto(self, token: str) -> str: ...
