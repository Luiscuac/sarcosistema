"""Reglas del caso de uso de laboratorio, independientes de HTTP y de SQLAlchemy."""
from datetime import date, time
from unittest.mock import AsyncMock

import pytest

from app.laboratorio.application.service import LaboratorioService
from app.laboratorio.domain.entities import (
    MuestraSolicitudNueva,
    PacienteNuevo,
    SolicitudNueva,
    TomaMuestraNueva,
    ValorResultadoEntrada,
)


class RepositorioEspia:
    """Registra las llamadas y devuelve valores predecibles."""

    def __init__(self):
        self.crear_paciente = AsyncMock(return_value="PAC-1")
        self.crear_solicitud = AsyncMock(return_value="SOL-1")
        self.recibir_muestra = AsyncMock(return_value="MUE-1")
        self.recibir_muestra_solicitud = AsyncMock(return_value="MUE-1")
        self.buscar_pacientes = AsyncMock(return_value=[])
        self.obtener_resultado = AsyncMock(return_value="RES-1")
        self.guardar_borrador = AsyncMock(return_value="BOR-1")
        self.publicar_resultado = AsyncMock(return_value="PUB-1")


@pytest.fixture
def servicio():
    repositorio = RepositorioEspia()
    return LaboratorioService(repositorio), repositorio


async def test_busqueda_recorta_el_termino_antes_de_consultar(servicio):
    caso, repositorio = servicio
    await caso.buscar_pacientes("  Paciente  ")
    repositorio.buscar_pacientes.assert_awaited_once_with("Paciente")


async def test_paciente_sin_documento_omite_los_campos_de_documento(servicio):
    caso, repositorio = servicio
    paciente = PacienteNuevo("  Paciente  ", date(1990, 1, 1), "M",
                             "CI", "12345678", sin_documento=True)
    await caso.crear_paciente(paciente, 7)
    guardado = repositorio.crear_paciente.await_args.args[0]
    assert guardado.nombre_completo == "Paciente"
    assert guardado.tipo_documento is None
    assert guardado.numero_documento is None


async def test_paciente_ni_documento_ni_marca_se_rechaza_sin_consultar(servicio):
    caso, repositorio = servicio
    paciente = PacienteNuevo("Paciente", date(1990, 1, 1), "M", None, None, sin_documento=False)
    with pytest.raises(ValueError, match="documento"):
        await caso.crear_paciente(paciente, 7)
    repositorio.crear_paciente.assert_not_awaited()


async def test_solicitud_sin_estudios_se_rechaza(servicio):
    caso, repositorio = servicio
    solicitud = _solicitud(tipo_estudio_ids=())
    with pytest.raises(ValueError, match="al menos un estudio"):
        await caso.crear_solicitud(solicitud, 7)
    repositorio.crear_solicitud.assert_not_awaited()


async def test_solicitud_no_repite_el_mismo_estudio(servicio):
    caso, repositorio = servicio
    solicitud = _solicitud(tipo_estudio_ids=(1, 1))
    with pytest.raises(ValueError, match="No repitas"):
        await caso.crear_solicitud(solicitud, 7)
    repositorio.crear_solicitud.assert_not_awaited()


async def test_solicitud_exige_medico_solicitante(servicio):
    caso, repositorio = servicio
    solicitud = _solicitud(medico_solicitante_nombre="   ")
    with pytest.raises(ValueError, match="profesional solicitante"):
        await caso.crear_solicitud(solicitud, 7)
    repositorio.crear_solicitud.assert_not_awaited()


@pytest.mark.parametrize(("hora_toma", "hora_no_registrada"), [
    (time(9, 30), True),   # hora marcada como no registrada pero informada
    (None, False),         # hora obligatoria ausente
])
async def test_muestra_con_hora_inconsistente_se_rechaza(servicio, hora_toma, hora_no_registrada):
    caso, repositorio = servicio
    toma = TomaMuestraNueva(5, "Sangre", date(2026, 10, 22), hora_toma, hora_no_registrada)
    with pytest.raises(ValueError, match="hora"):
        await caso.recibir_muestra(toma, 7)
    repositorio.recibir_muestra.assert_not_awaited()


async def test_muestra_de_solicitud_rechaza_seleccion_invalida(servicio):
    caso, repositorio = servicio
    for estudio_ids in [(), (11, 11)]:
        toma = MuestraSolicitudNueva(4, estudio_ids, "Sangre", date(2026, 10, 22),
                                     time(9, 30), False)
        with pytest.raises(ValueError, match="estudios distintos"):
            await caso.recibir_muestra_solicitud(toma, 7)
    repositorio.recibir_muestra_solicitud.assert_not_awaited()


async def test_muestra_valida_llega_al_repositorio_con_sus_datos(servicio):
    caso, repositorio = servicio
    toma = TomaMuestraNueva(5, "Sangre", date(2026, 10, 22), time(9, 30), False)
    assert await caso.recibir_muestra(toma, 7) == "MUE-1"
    assert repositorio.recibir_muestra.await_args.args[1] == 7


async def test_resultado_y_borrador_delegan_en_el_repositorio(servicio):
    caso, repositorio = servicio
    assert await caso.obtener_resultado(5) == "RES-1"
    assert await caso.publicar_resultado(5, 7) == "PUB-1"
    valores = (ValorResultadoEntrada(parametro_id=1, valor="90"),)
    assert await caso.guardar_borrador(5, valores, "Observación", 7) == "BOR-1"
    repositorio.guardar_borrador.assert_awaited_once_with(5, valores, "Observación", 7)


def _solicitud(tipo_estudio_ids=(1,), medico_solicitante_nombre="Dra. Ficticia"):
    from datetime import datetime, timezone

    return SolicitudNueva(
        paciente_id=1, tipo_estudio_ids=tipo_estudio_ids,
        fecha_solicitud=datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc),
        referencia_papel_formulario=None, establecimiento_solicitante_nombre=None,
        medico_solicitante_nombre=medico_solicitante_nombre, diagnostico_principal=None,
        prioridad="sin_prioridad", clave_idempotencia="clave",
    )
