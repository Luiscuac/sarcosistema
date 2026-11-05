"""Validación de los claims obligatorios de los tokens de sesión."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.accesos.infrastructure.security.jwt_service import JwtTokenService

SECRET = "clave-ficticia-para-pruebas-de-jwt"


def test_token_emitido_conserva_el_sujeto_como_string():
    servicio = JwtTokenService(SECRET)

    assert servicio.obtener_sujeto(servicio.emitir("7", "medico")) == "7"


def test_token_firmado_sin_expiracion_se_rechaza():
    token = jwt.encode({"sub": "7", "rol": "medico"}, SECRET, algorithm="HS256")

    with pytest.raises(ValueError, match="Token inválido"):
        JwtTokenService(SECRET).obtener_sujeto(token)


@pytest.mark.parametrize("sujeto", [7, 7.5, True, False, None, [], {}, ["7"]])
def test_token_firmado_con_sujeto_no_string_se_rechaza(sujeto):
    token = jwt.encode(
        {"sub": sujeto, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        SECRET,
        algorithm="HS256",
    )

    with pytest.raises(ValueError, match="Token inválido"):
        JwtTokenService(SECRET).obtener_sujeto(token)


def test_token_firmado_sin_sujeto_se_rechaza():
    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        SECRET,
        algorithm="HS256",
    )

    with pytest.raises(ValueError, match="Token inválido"):
        JwtTokenService(SECRET).obtener_sujeto(token)
