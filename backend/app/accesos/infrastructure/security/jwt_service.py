"""Emisión y validación de tokens JWT."""
from datetime import datetime, timedelta, timezone

import jwt

ALGORITHM = "HS256"


class JwtTokenService:
    def __init__(self, secret_key: str, minutos_expiracion: int = 60):
        self.secret_key = secret_key
        self.minutos_expiracion = minutos_expiracion

    def emitir(self, usuario_id: str, rol: str) -> str:
        payload = {
            "sub": usuario_id,
            "rol": rol,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=self.minutos_expiracion),
        }
        return jwt.encode(payload, self.secret_key, algorithm=ALGORITHM)

    def obtener_sujeto(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return payload["sub"]
        except (jwt.PyJWTError, KeyError, TypeError) as exc:
            raise ValueError("Token inválido") from exc
