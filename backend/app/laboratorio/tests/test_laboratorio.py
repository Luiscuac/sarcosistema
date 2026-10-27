"""Pruebas de validación del contrato de recepción de muestras."""

from datetime import date, time
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.laboratorio.presentation.schemas import CrearPacienteRequest, RecibirMuestraRequest, RecibirMuestraSolicitudRequest
from app.laboratorio.domain.entities import AccionAuditoria, MuestraSolicitudNueva
from app.laboratorio.application.service import LaboratorioService
from app.laboratorio.infrastructure.persistence.repository import (
    SqlAlchemyExamenRepository, campos_obligatorios_faltantes,
)
from app.laboratorio.presentation.router import get_service
from app.main import app


def test_acciones_de_auditoria_usadas_existen_en_la_restriccion_del_esquema():
    acciones_permitidas = {
        "crear", "modificar", "publicar", "rectificar", "invalidar",
        "anular", "consultar", "acceder", "exportar", "importar",
    }

    assert {accion.value for accion in AccionAuditoria} <= acciones_permitidas


def test_recibir_muestra_acepta_hora_registrada():
    solicitud = RecibirMuestraRequest(
        tipo_muestra="  Orina  ",
        fecha_toma=date(2026, 10, 22),
        hora_toma=time(9, 30),
        hora_no_registrada=False,
    )

    assert solicitud.tipo_muestra == "Orina"


def test_recibir_muestra_acepta_hora_no_registrada():
    solicitud = RecibirMuestraRequest(
        tipo_muestra="Sangre",
        fecha_toma=date(2026, 10, 22),
        hora_toma=None,
        hora_no_registrada=True,
    )

    assert solicitud.hora_no_registrada is True


@pytest.mark.parametrize(
    ("hora_toma", "hora_no_registrada"),
    [(None, False), (time(9, 30), True)],
)
def test_recibir_muestra_rechaza_combinacion_de_hora_inconsistente(
    hora_toma, hora_no_registrada
):
    with pytest.raises(ValidationError, match="hora"):
        RecibirMuestraRequest(
            tipo_muestra="Sangre",
            fecha_toma=date(2026, 10, 22),
            hora_toma=hora_toma,
            hora_no_registrada=hora_no_registrada,
        )


def test_recibir_muestra_rechaza_tipo_vacio():
    with pytest.raises(ValidationError, match="tipo de muestra"):
        RecibirMuestraRequest(
            tipo_muestra="   ",
            fecha_toma=date(2026, 10, 22),
            hora_toma=time(9, 30),
            hora_no_registrada=False,
        )


def test_muestra_de_solicitud_acepta_varios_estudios():
    solicitud = RecibirMuestraSolicitudRequest(
        estudio_ids=[11, 12],
        tipo_muestra="  Sangre  ",
        fecha_toma=date(2026, 10, 22),
        hora_toma=time(9, 30),
    )
    assert solicitud.estudio_ids == [11, 12]
    assert solicitud.tipo_muestra == "Sangre"


@pytest.mark.parametrize("ids", [[], [11, 11], [0]])
def test_muestra_de_solicitud_rechaza_seleccion_invalida(ids):
    with pytest.raises(ValidationError):
        RecibirMuestraSolicitudRequest(
            estudio_ids=ids,
            tipo_muestra="Sangre",
            fecha_toma=date(2026, 10, 22),
            hora_toma=time(9, 30),
        )


@pytest.mark.asyncio
async def test_servicio_envia_una_muestra_para_varios_estudios():
    class RepositorioFalso:
        async def recibir_muestra_solicitud(self, toma, usuario_id):
            assert toma.estudio_ids == (11, 12)
            assert usuario_id == 7
            return "MUE-PRUEBA"

    toma = MuestraSolicitudNueva(1, (11, 12), "Sangre", date(2026, 10, 22), time(9, 30), False)
    assert await LaboratorioService(RepositorioFalso()).recibir_muestra_solicitud(toma, 7) == "MUE-PRUEBA"


@pytest.mark.asyncio
@pytest.mark.parametrize("ids", [(), (11, 11)])
async def test_repositorio_no_crea_muestra_sin_seleccion_valida(ids):
    toma = MuestraSolicitudNueva(1, ids, "Sangre", date(2026, 10, 22), time(9, 30), False)
    db = SimpleNamespace(execute=AsyncMock())
    with pytest.raises(ValueError, match="estudios distintos"):
        await SqlAlchemyExamenRepository(db).recibir_muestra_solicitud(toma, 7)
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_endpoint_registra_una_muestra_para_estudios_de_la_solicitud(client, usuarios):
    class ServicioFalso:
        async def recibir_muestra_solicitud(self, toma, usuario_id):
            assert toma.solicitud_id == 4
            assert toma.estudio_ids == (11, 12)
            assert usuario_id == usuarios.id
            return "MUE-PRUEBA"

    app.dependency_overrides[get_service] = lambda: ServicioFalso()
    try:
        login = await client.post("/accesos/login", json={
            "identificador_acceso": "laboratorio_prueba", "password": "clave-de-prueba",
        })
        token = login.json()["access_token"]
        respuesta = await client.post(
            "/laboratorio/solicitudes/4/muestras",
            headers={"Authorization": f"Bearer {token}"},
            json={"estudio_ids": [11, 12], "tipo_muestra": "Sangre",
                  "fecha_toma": "2026-10-22", "hora_toma": "09:30:00"},
        )
        assert respuesta.status_code == 201
        assert respuesta.json() == {"referencia_muestra": "MUE-PRUEBA"}
    finally:
        app.dependency_overrides.pop(get_service, None)


@pytest.mark.asyncio
async def test_registro_de_muestra_requiere_sesion(client, usuarios):
    respuesta = await client.post("/laboratorio/solicitudes/4/muestras", json={
        "estudio_ids": [11], "tipo_muestra": "Sangre",
        "fecha_toma": "2026-10-22", "hora_toma": "09:30:00",
    })
    assert respuesta.status_code == 401


def test_identificadores_del_registro_mensual_son_opcionales_y_se_normalizan():
    paciente = CrearPacienteRequest(
        nombre_completo="Paciente de prueba",
        fecha_nacimiento=date(1990, 1, 1),
        sexo="F",
        tipo_documento="CI",
        numero_documento="123456",
        historia_clinica="  HC-123  ",
        codigo_externo="  LAB-5  ",
    )

    assert paciente.historia_clinica == "HC-123"
    assert paciente.codigo_externo == "LAB-5"


def test_identificador_externo_demasiado_largo_se_rechaza():
    with pytest.raises(ValidationError, match="historia_clinica"):
        CrearPacienteRequest(
            nombre_completo="Paciente de prueba",
            fecha_nacimiento=date(1990, 1, 1),
            sexo="F",
            sin_documento=True,
            historia_clinica="A" * 81,
        )


def test_publicacion_exige_valores_obligatorios_no_vacios_y_acepta_cero():
    parametros = [SimpleNamespace(id=1, nombre="Glucosa", obligatorio=True),
                  SimpleNamespace(id=2, nombre="Observación", obligatorio=False)]
    vacio = SimpleNamespace(parametro_id=1, valor_entero=None, valor_decimal=None,
                            valor_texto="", valor_cualitativo=None)
    assert campos_obligatorios_faltantes(parametros, [vacio]) == ["Glucosa"]

    cero = SimpleNamespace(parametro_id=1, valor_entero=None, valor_decimal=Decimal("0"),
                           valor_texto=None, valor_cualitativo=None)
    assert campos_obligatorios_faltantes(parametros, [cero]) == []
