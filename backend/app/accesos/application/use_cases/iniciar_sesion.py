from app.accesos.application.errors.invalid_credentials import CredencialesInvalidas
from app.accesos.application.ports.password_verifier import PasswordVerifier
from app.accesos.application.ports.token_service import TokenService
from app.accesos.application.ports.usuario_repository import UsuarioRepository
from app.accesos.application.results.session import Sesion


class IniciarSesion:
    def __init__(
        self,
        usuarios: UsuarioRepository,
        password: PasswordVerifier,
        tokens: TokenService,
    ):
        self.usuarios = usuarios
        self.password = password
        self.tokens = tokens

    async def ejecutar(self, identificador: str, password: str) -> Sesion:
        usuario = await self.usuarios.buscar_por_identificador(identificador)
        if (
            usuario is None
            or not usuario.activo
            or usuario.contrasena_hash is None
            or not self.password.verificar(password, usuario.contrasena_hash)
        ):
            raise CredencialesInvalidas
        return Sesion(self.tokens.emitir(str(usuario.id), usuario.rol))
