"""HU-N22/N23: login y acceso al módulo de laboratorio."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.accesos.infrastructure.persistence import repository as usuario_repository
from app.accesos.domain.entities import Usuario
from app.config.database import get_db
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def usuarios(monkeypatch):
    password_hasher = Argon2PasswordHasher()
    password_hash = password_hasher.hashear("clave-de-prueba")
    usuario = Usuario(
        id=7,
        identificador_acceso="laboratorio_prueba",
        contrasena_hash=password_hash,
        rol="laboratorio",
        activo=True,
    )

    async def por_identificador(_repository, identificador):
        return usuario if identificador == usuario.identificador_acceso else None

    async def por_id(_repository, usuario_id):
        return usuario if usuario_id == usuario.id else None

    async def db_falsa():
        yield object()

    monkeypatch.setattr(
        usuario_repository.SqlAlchemyUsuarioRepository,
        "buscar_por_identificador",
        por_identificador,
    )
    monkeypatch.setattr(
        usuario_repository.SqlAlchemyUsuarioRepository,
        "buscar_por_id",
        por_id,
    )
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
    usuarios.rol = "medico"
    respuesta = await client.post("/accesos/login", json={
        "identificador_acceso": "laboratorio_prueba", "password": "clave-de-prueba",
    })
    token = respuesta.json()["access_token"]
    examen = await client.get("/examenes/1", headers={"Authorization": f"Bearer {token}"})
    assert examen.status_code == 403


def test_hash_corrupto_no_autentica():
    assert Argon2PasswordHasher().verificar("clave-de-prueba", "hash-invalido") is False
