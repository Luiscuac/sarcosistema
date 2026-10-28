"""Endpoints de registros de prueba del transcriptor (datos ficticios, sin BD clínica)."""
import pytest

from app.ia.transcriptor.application.use_cases.listar_registros_prueba import ListarRegistrosPrueba
from app.ia.transcriptor.domain.entities import RegistroPrueba
from app.ia.transcriptor.infrastructure.registro_repository import RepositorioRegistrosPrueba


def test_repositorio_expone_registros_ficticios_y_los_busca_por_id():
    repositorio = RepositorioRegistrosPrueba()
    registros = repositorio.listar()
    assert len(registros) == 3
    assert [registro.id for registro in registros] == ["demo-001", "demo-002", "demo-003"]
    assert repositorio.obtener("demo-001") == registros[0]
    assert repositorio.obtener("no-existe") is None


def test_caso_de_uso_delega_en_el_repositorio():
    caso = ListarRegistrosPrueba(RepositorioRegistrosPrueba())
    assert len(caso.ejecutar()) == 3
    assert caso.obtener("demo-002") == RegistroPrueba(
        "demo-002", "PA-TEST-002", "Paciente de prueba Dos",
        "2026-01-16", "Glucosa", "92", "mg/dL",
    )


@pytest.mark.asyncio
async def test_listar_registros_requiere_sesion(client):
    respuesta = await client.get("/ia/transcriptor/registros")
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_listar_y_leer_un_registro(client, usuarios):
    login = await client.post("/accesos/login", json={
        "identificador_acceso": "laboratorio_prueba", "password": "clave-de-prueba",
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    listado = await client.get("/ia/transcriptor/registros", headers=headers)
    assert listado.status_code == 200
    assert len(listado.json()) == 3
    assert listado.json()[0]["codigo"] == "PA-TEST-001"

    detalle = await client.get("/ia/transcriptor/registros/demo-001", headers=headers)
    assert detalle.status_code == 200
    assert detalle.json()["nombre"] == "Paciente de prueba Uno"
    assert detalle.json()["unidad"] == "g/dL"


@pytest.mark.asyncio
async def test_registro_inexistente_devuelve_404(client, usuarios):
    login = await client.post("/accesos/login", json={
        "identificador_acceso": "laboratorio_prueba", "password": "clave-de-prueba",
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    respuesta = await client.get("/ia/transcriptor/registros/inexistente", headers=headers)
    assert respuesta.status_code == 404
