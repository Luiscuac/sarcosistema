from app.accesos.application.errors.access_denied import AccesoNoAutorizado
from app.accesos.application.ports.token_service import TokenService
from app.accesos.application.ports.usuario_repository import UsuarioRepository
from app.accesos.domain.entities import Usuario


class ObtenerUsuarioActual:
    def __init__(self, usuarios: UsuarioRepository, tokens: TokenService):
        self.usuarios = usuarios
        self.tokens = tokens

    async def ejecutar(self, token: str) -> Usuario:
        try:
            usuario_id = int(self.tokens.obtener_sujeto(token))
            if usuario_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise AccesoNoAutorizado from None

        usuario = await self.usuarios.buscar_por_id(usuario_id)
        if usuario is None or not usuario.activo:
            raise AccesoNoAutorizado
        return usuario
