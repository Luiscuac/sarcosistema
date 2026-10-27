"""Fixtures compartidas por las pruebas de todos los módulos."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.accesos.domain.entities import Usuario
from app.accesos.infrastructure.persistence import repository as usuario_repository
from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import get_db
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def usuarios(monkeypatch):
    usuario = Usuario(
        id=7,
        identificador_acceso="laboratorio_prueba",
        contrasena_hash=Argon2PasswordHasher().hashear("clave-de-prueba"),
        rol="laboratorio",
        activo=True,
    )

    async def por_identificador(_repository, identificador):
        return usuario if identificador == usuario.identificador_acceso else None

    async def por_id(_repository, usuario_id):
        return usuario if usuario_id == usuario.id else None

    async def db_falsa():
        yield object()

    monkeypatch.setattr(usuario_repository.SqlAlchemyUsuarioRepository, "buscar_por_identificador", por_identificador)
    monkeypatch.setattr(usuario_repository.SqlAlchemyUsuarioRepository, "buscar_por_id", por_id)
    app.dependency_overrides[get_db] = db_falsa
    yield usuario
    app.dependency_overrides.clear()
