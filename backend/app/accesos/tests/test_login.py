"""HU-N22/N23: login y acceso al módulo de laboratorio."""
import pytest

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher


@pytest.mark.asyncio
async def test_login_correcto_y_acceso_protegido(client, usuarios):
    respuesta = await client.post("/accesos/login", json={
        "identificador_acceso": "laboratorio_prueba", "password": "clave-de-prueba",
    })
    assert respuesta.status_code == 200
    token = respuesta.json()["access_token"]
    assert respuesta.json()["token_type"] == "bearer"
    perfil = await client.get("/accesos/yo", headers={"Authorization": f"Bearer {token}"})
    assert perfil.status_code == 200
    assert perfil.json()["rol"] == "laboratorio"


@pytest.mark.asyncio
async def test_credenciales_incorrectas(client, usuarios):
    for identificador, password in [
        ("laboratorio_prueba", "incorrecta"), ("desconocido", "clave-de-prueba")
    ]:
        respuesta = await client.post("/accesos/login", json={
            "identificador_acceso": identificador, "password": password,
        })
        assert respuesta.status_code == 401
        assert respuesta.json()["detail"] == "Credenciales incorrectas"


@pytest.mark.asyncio
async def test_sin_token_o_token_invalido(client, usuarios):
    assert (await client.get("/accesos/yo")).status_code == 401
    respuesta = await client.get("/accesos/yo", headers={"Authorization": "Bearer invalido"})
    assert respuesta.status_code == 401
    assert (await client.get("/laboratorio/catalogo/estudios")).status_code == 401


@pytest.mark.asyncio
async def test_otra_funcion_no_accede_laboratorio(client, usuarios):
    usuarios.rol = "medico"
    respuesta = await client.post("/accesos/login", json={
        "identificador_acceso": "laboratorio_prueba", "password": "clave-de-prueba",
    })
    token = respuesta.json()["access_token"]
    examen = await client.get("/laboratorio/catalogo/estudios", headers={"Authorization": f"Bearer {token}"})
    assert examen.status_code == 403


def test_hash_corrupto_no_autentica():
    assert Argon2PasswordHasher().verificar("clave-de-prueba", "hash-invalido") is False
