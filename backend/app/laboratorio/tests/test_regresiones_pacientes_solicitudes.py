"""Regresiones de identificación, búsqueda literal y reenvío de solicitudes."""
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.laboratorio.application.service import LaboratorioService
from app.laboratorio.domain.entities import PacienteNuevo, SolicitudNueva
from app.laboratorio.infrastructure.persistence.models import Solicitud, EstudioSolicitado
from app.laboratorio.infrastructure.persistence.repository import SqlAlchemyExamenRepository
from app.laboratorio.presentation.schemas import CrearPacienteRequest
from app.shared.entities.paciente import Paciente


def paciente_request(**cambios):
    return CrearPacienteRequest(**{
        "nombre_completo": "Paciente ficticia", "fecha_nacimiento": date(1990, 1, 1),
        "sexo": "F", "tipo_documento": "CI", "numero_documento": "123456",
        **cambios,
    })


@pytest.mark.parametrize("cambios", [
    {"tipo_documento": "   "}, {"numero_documento": " \t "},
])
def test_documento_en_blanco_se_rechaza_tras_normalizar(cambios):
    with pytest.raises(ValidationError, match="documento"):
        paciente_request(**cambios)


def test_documentos_con_espacios_tienen_la_misma_identidad():
    paciente = paciente_request(tipo_documento=" CI ", numero_documento=" 123456 ")
    assert (paciente.tipo_documento, paciente.numero_documento) == ("CI", "123456")


def test_sin_documento_acepta_campos_vacios_normalizados():
    paciente = paciente_request(sin_documento=True, tipo_documento=" ", numero_documento=" ")
    assert paciente.tipo_documento is None
    assert paciente.numero_documento is None


def test_fecha_nacimiento_futura_se_rechaza():
    with pytest.raises(ValidationError, match="nacimiento"):
        paciente_request(fecha_nacimiento=date.today() + timedelta(days=1))


def test_paciente_conserva_opcionales_validos_y_acepta_nacimiento_hoy():
    paciente = paciente_request(fecha_nacimiento=date.today(), historia_clinica=" HC-1 ",
                                 codigo_externo=" EXT-1 ")
    assert paciente.fecha_nacimiento == date.today()
    assert (paciente.historia_clinica, paciente.codigo_externo) == ("HC-1", "EXT-1")


async def test_busqueda_vacia_no_consulta_el_repositorio():
    repositorio = SimpleNamespace(buscar_pacientes=AsyncMock(return_value=["no exponer"]))
    assert await LaboratorioService(repositorio).buscar_pacientes(" \t ") == []
    repositorio.buscar_pacientes.assert_not_awaited()


@pytest.mark.parametrize("cambios", [
    {"tipo_documento": " "}, {"numero_documento": " "},
    {"fecha_nacimiento": date.today() + timedelta(days=1)},
])
async def test_servicio_rechaza_paciente_invalido_antes_de_guardar(cambios):
    paciente = PacienteNuevo("Paciente ficticia", date(1990, 1, 1), "F", "CI", "123", False)
    repositorio = SimpleNamespace(crear_paciente=AsyncMock())
    with pytest.raises(ValueError):
        await LaboratorioService(repositorio).crear_paciente(replace(paciente, **cambios), 7)
    repositorio.crear_paciente.assert_not_awaited()


async def test_servicio_normaliza_documento_sin_perder_opcionales():
    paciente = PacienteNuevo("Paciente ficticia", date(1990, 1, 1), "F", " CI ", " 123 ",
                            False, "HC-1", "EXT-1")
    repositorio = SimpleNamespace(crear_paciente=AsyncMock())
    await LaboratorioService(repositorio).crear_paciente(paciente, 7)
    guardado, actor = repositorio.crear_paciente.await_args.args
    assert (guardado.tipo_documento, guardado.numero_documento) == ("CI", "123")
    assert (guardado.historia_clinica, guardado.codigo_externo, actor) == ("HC-1", "EXT-1", 7)


@pytest.fixture
def busqueda_db():
    # SQL real en memoria: no toca PostgreSQL ni sus datos.
    engine = create_engine("sqlite://")
    Paciente.__table__.create(engine)
    with Session(engine) as session:
        nombres = ["Paciente comun", "Paciente 10%", "Paciente A_B", "Paciente A/B",
                   "Paciente AXB"]
        session.add_all([
            Paciente(id=i, codigo_paciente=f"PAC-{i}", nombre_completo=nombre,
                     numero_documento=None, sin_documento=True,
                     fecha_nacimiento=date(1990, 1, 1), sexo="F", estado="activo")
            for i, nombre in enumerate(nombres, 1)
        ])
        session.flush()

        class SesionAsincrona:
            async def execute(self, statement):
                return session.execute(statement)

        yield SesionAsincrona()
    engine.dispose()


@pytest.mark.parametrize(("termino", "ids"), [
    ("%", [2]), ("_", [3]), ("A/B", [4]), ("Paciente", [2, 4, 5, 3, 1]),
    ("   ", []), ("", []),
])
async def test_busqueda_interpreta_comodines_como_texto_literal(busqueda_db, termino, ids):
    encontrados = await SqlAlchemyExamenRepository(busqueda_db).buscar_pacientes(termino)
    assert [paciente.id for paciente in encontrados] == ids


@pytest.fixture
def replay():
    entrada = SolicitudNueva(
        paciente_id=1, tipo_estudio_ids=(11, 12),
        fecha_solicitud=datetime(2026, 10, 22, 10, tzinfo=timezone.utc),
        referencia_papel_formulario="PAP-1", establecimiento_solicitante_nombre="Centro ficticio",
        medico_solicitante_nombre="Dra. Ficticia", diagnostico_principal="Control",
        prioridad="sin_prioridad", clave_idempotencia="clave-regresion",
    )
    original = Solicitud(
        id=4, referencia="SOL-4", paciente_id=1, fecha_solicitud=entrada.fecha_solicitud,
        referencia_papel_formulario="PAP-1",
        establecimiento_solicitante_nombre_snapshot="Centro ficticio",
        medico_solicitante_nombre_snapshot="Dra. Ficticia", diagnostico_principal="Control",
        prioridad="sin_prioridad", clave_idempotencia=entrada.clave_idempotencia, created_by=7,
    )
    estudios = [(EstudioSolicitado(id=i, referencia=f"EST-{i}", tipo_estudio_id=tipo,
                                 estado="pendiente_muestra"), f"Estudio {tipo}")
                for i, tipo in [(21, 11), (22, 12)]]
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[
            SimpleNamespace(scalar_one_or_none=lambda: original),
            SimpleNamespace(all=lambda: estudios),
        ]),
        get=AsyncMock(return_value=SimpleNamespace(nombre_completo="Paciente ficticia")),
        add=Mock(), flush=AsyncMock(),
    )
    return entrada, original, db


@pytest.mark.parametrize("cambios", [
    {"paciente_id": 2}, {"tipo_estudio_ids": (11,)}, {"prioridad": "urgente"},
    {"medico_solicitante_nombre": "Dr. Otro"}, {"diagnostico_principal": None},
    {"establecimiento_solicitante_nombre": "Otro centro"},
    {"referencia_papel_formulario": "PAP-2"},
    {"fecha_solicitud": datetime(2026, 10, 23, 10, tzinfo=timezone.utc)},
])
async def test_replay_con_datos_distintos_rechaza_sin_modificar_original(replay, cambios):
    entrada, original, db = replay
    antes = dict(original.__dict__)
    with pytest.raises(ValueError, match="clave de envío"):
        await SqlAlchemyExamenRepository(db).crear_solicitud(replace(entrada, **cambios), 7)
    assert original.__dict__ == antes
    db.add.assert_not_called()
    db.flush.assert_not_awaited()


async def test_replay_de_otro_actor_se_rechaza(replay):
    entrada, original, db = replay
    with pytest.raises(ValueError, match="clave de envío"):
        await SqlAlchemyExamenRepository(db).crear_solicitud(entrada, 8)
    assert original.created_by == 7
    db.add.assert_not_called()
    db.flush.assert_not_awaited()


async def test_replay_identico_admite_orden_distinto_y_profesional_normalizado(replay):
    entrada, original, db = replay
    resultado = await SqlAlchemyExamenRepository(db).crear_solicitud(
        replace(entrada, tipo_estudio_ids=(12, 11), medico_solicitante_nombre=" Dra. Ficticia "), 7,
    )
    assert resultado.id == 4
    assert resultado.prioridad == "sin_prioridad"
    assert [estudio.id for estudio in resultado.estudios] == [21, 22]
    db.add.assert_not_called()
    db.flush.assert_not_awaited()


async def test_reintento_sin_fecha_explicita_conserva_fecha_original(replay):
    from uuid import uuid4
    from app.accesos.domain.entities import Usuario
    from app.laboratorio.presentation.router import crear_solicitud
    from app.laboratorio.presentation.schemas import CrearSolicitudRequest

    entrada, original, db = replay
    datos = CrearSolicitudRequest(paciente_id=1, tipo_estudio_ids=[11, 12],
        referencia_papel_formulario='PAP-1', establecimiento_solicitante_nombre='Centro ficticio',
        medico_solicitante_nombre='Dra. Ficticia', diagnostico_principal='Control',
        prioridad='sin_prioridad', clave_idempotencia=uuid4())
    assert datos.fecha_solicitud != original.fecha_solicitud
    resultado = await crear_solicitud(datos, Usuario(7, 'lab_ficticio', 'laboratorio', True),
        LaboratorioService(SqlAlchemyExamenRepository(db)))
    assert resultado.id == original.id
    assert resultado.fecha_solicitud == original.fecha_solicitud
