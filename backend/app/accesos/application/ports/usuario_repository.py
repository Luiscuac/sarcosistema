from typing import Protocol

from app.accesos.domain.entities import Usuario


class UsuarioRepository(Protocol):
    async def buscar_por_identificador(self, identificador: str) -> Usuario | None: ...

    async def buscar_por_id(self, usuario_id: int) -> Usuario | None: ...
