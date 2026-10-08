"""
Logica de negocio del modulo accesos (HU-N22, HU-N23).
Autenticar usuario y generar token JWT.
"""
from fastapi import HTTPException, status

from app.accesos.repository import UsuarioRepository
from app.accesos.security import verificar_password, crear_token
from app.config.settings import settings


class AccesoService:
    def __init__(self, repository: UsuarioRepository):
        self.repository = repository

    async def autenticar(self, identificador_acceso: str, contrasena: str) -> dict:
        """
        Busca al usuario, verifica su contrasena y genera un JWT.
        Devuelve un dict con access_token, rol y nombre_usuario.
        """
        usuario = await self.repository.obtener_por_identificador(identificador_acceso)

        if usuario is None or not verificar_password(contrasena, usuario.contrasena_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if usuario.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La cuenta no esta activa. Contacte al responsable de accesos.",
            )

        rol = await self.repository.obtener_rol(usuario.rol_id)
        codigo_rol = rol.codigo if rol else "sin_rol"

        token = crear_token(
            sub=str(usuario.id),
            rol=codigo_rol,
            secret_key=settings.jwt_secret_key,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "rol": codigo_rol,
            "nombre_usuario": usuario.identificador_acceso,
        }
