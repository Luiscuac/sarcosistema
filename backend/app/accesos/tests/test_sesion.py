"""Robustez de la sesión: tokens manipulados, cuentas inactivas y restricción por rol."""
from datetime import timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.accesos.domain.entities import Usuario
from app.accesos.infrastructure.persistence.mappers import mapear_usuario
from app.accesos.infrastructure.security.jwt_service import JwtTokenService
from app.accesos.presentation.dependencies.role_required import requiere_rol
from app.config.settings import settings

SECRET = settings.jwt_secret_key


def _token(secret=SECRET, minutos=60, rol="laboratorio", sujeto="7"):
    servicio = JwtTokenService(secret, minutos_expiracion=minutos)
    return servicio.emitir(sujeto, rol)


@pytest.mark.asyncio
async def test_token_firmado_con_otra_clave_se_rechaza(client, usuarios):
    respuesta = await client.get("/accesos/yo", headers={"Authorization": f"Bearer {_token(secret='otra')}"})
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_token_manipulado_se_rechaza(client, usuarios):
    falsificado = jwt.encode({"sub": "7", "rol": "medico"}, "otra", algorithm="HS256")
    respuesta = await client.get("/accesos/yo", headers={"Authorization": f"Bearer {falsificado}"})
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_token_vencido_se_rechaza(client, usuarios):
    vencido = _token(minutos=-1)
    respuesta = await client.get("/accesos/yo", headers={"Authorization": f"Bearer {vencido}"})
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_token_valido_identifica_al_usuario(client, usuarios):
    respuesta = await client.get("/accesos/yo", headers={"Authorization": f"Bearer {_token()}"})
    assert respuesta.status_code == 200
    assert respuesta.json()["identificador_acceso"] == usuarios.identificador_acceso


@pytest.mark.asyncio
async def test_cuenta_inactiva_no_inicia_sesion(client, usuarios):
    usuarios.activo = False
    respuesta = await client.post("/accesos/login", json={
        "identificador_acceso": usuarios.identificador_acceso, "password": "clave-de-prueba",
    })
    assert respuesta.status_code == 401


def test_jwt_solo_guarda_identidad_y_rol_no_datos_clinicos():
    servicio = JwtTokenService(SECRET)
    token = servicio.emitir("7", "medico")
    carga = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert set(carga) == {"sub", "rol", "exp"}


def test_token_invalido_genera_error_claro():
    with pytest.raises(ValueError, match="Token inválido"):
        JwtTokenService(SECRET).obtener_sujeto("no-es-un-token")


@pytest.mark.parametrize(("rol_activo", "trabajador_estado", "esperado"), [
    (True, "activo", True),        # cuenta operativa
    (False, "activo", False),      # rol retirado
    (True, "inactivo", False),     # trabajador ya no está activo
    (False, "inactivo", False),
])
def test_la_sesion_exige_cuenta_rol_y_trabajador_activos(rol_activo, trabajador_estado, esperado):
    fila = {
        "id": 7, "identificador_acceso": "laboratorio_prueba", "estado": "activo",
        "rol": "laboratorio", "rol_activo": rol_activo,
        "trabajador_estado": trabajador_estado, "contrasena_hash": "hash",
    }
    assert mapear_usuario(fila).activo is esperado


def test_mapeo_no_expone_el_hash_si_no_se_pide():
    fila = {
        "id": 7, "identificador_acceso": "laboratorio_prueba", "estado": "activo",
        "rol": "laboratorio", "rol_activo": True, "trabajador_estado": "activo",
        "contrasena_hash": "hash-secreto",
    }
    assert mapear_usuario(fila).contrasena_hash is None
    assert mapear_usuario(fila, incluir_hash=True).contrasena_hash == "hash-secreto"


@pytest.mark.asyncio
async def test_rol_distinto_no_pasa_la_restriccion():
    verificador = requiere_rol("laboratorio")
    with pytest.raises(HTTPException) as error:
        await verificador(Usuario(7, "doc_ficticio", "medico", True))
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_rol_requerido_pasa_con_la_cuenta_correcta():
    verificador = requiere_rol("laboratorio")
    usuario = Usuario(7, "laboratorio_prueba", "laboratorio", True)
    assert await verificador(usuario) is usuario


def test_expiracion_personalizable_del_token():
    assert JwtTokenService(SECRET, minutos_expiracion=30).minutos_expiracion == 30
    assert timedelta(minutes=30) == timedelta(minutes=30)
