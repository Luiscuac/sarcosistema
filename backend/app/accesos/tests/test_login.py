"""HU-N22/N23: login y acceso al módulo de laboratorio."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.accesos import dependencies, router
from app.accesos.security import hashear_password, verificar_password
from app.config.database import get_db
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def usuarios(monkeypatch):
    password_hash = hashear_password("clave-de-prueba")
    usuario = {
        "id": 7, "identificador_acceso": "laboratorio_prueba",
        "contrasena_hash": password_hash, "estado": "activo",
        "rol": "laboratorio", "rol_activo": True,
        "trabajador_estado": "activo",
    }

    async def por_identificador(_db, identificador):
        return usuario if identificador == usuario["identificador_acceso"] else None

    async def por_id(_db, usuario_id):
        return usuario if usuario_id == usuario["id"] else None

    async def db_falsa():
        yield object()

    monkeypatch.setattr(router, "buscar_usuario", por_identificador)
    monkeypatch.setattr(dependencies, "buscar_usuario_por_id", por_id)
    app.dependency_overrides[get_db] = db_falsa
    yield usuario
    app.dependency_overrides.clear()


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
    assert (await client.get("/examenes/1")).status_code == 401


@pytest.mark.asyncio
async def test_otra_funcion_no_accede_laboratorio(client, usuarios):
    usuarios["rol"] = "medico"
    respuesta = await client.post("/accesos/login", json={
        "identificador_acceso": "laboratorio_prueba", "password": "clave-de-prueba",
    })
    token = respuesta.json()["access_token"]
    examen = await client.get("/examenes/1", headers={"Authorization": f"Bearer {token}"})
    assert examen.status_code == 403


def test_hash_corrupto_no_autentica():
    assert verificar_password("clave-de-prueba", "hash-invalido") is False
