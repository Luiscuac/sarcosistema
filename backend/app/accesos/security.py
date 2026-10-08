"""
JWT y hash de contrasenas (Argon2id).
"""
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

ALGORITHM = "HS256"
ph = PasswordHasher()


def hashear_password(password: str) -> str:
    return ph.hash(password)


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return ph.verify(hash_guardado, password)
    except (InvalidHashError, VerificationError):
        return False


def crear_token(sub: str, rol: str, secret_key: str, minutos_expiracion: int = 60) -> str:
    payload = {
        "sub": sub,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutos_expiracion),
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)
