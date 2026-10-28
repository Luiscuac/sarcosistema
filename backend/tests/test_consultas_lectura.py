from types import SimpleNamespace

import pytest

from app.consultas.application.use_cases.consultar_pacientes import ConsultarPacientes
from app.consultas.application.use_cases.consultar_historial import ConsultarHistorial
from app.consultas.infrastructure.persistence.repository import SqlAlchemyConsultaRepository, presentar_consulta


@pytest.mark.asyncio
async def test_busqueda_normaliza_termino_y_pagina():
    class Repo:
        async def buscar_pacientes(self, buscar, pagina, limite):
            return {'items': [], 'total': 0, 'pagina': pagina, 'limite': limite, 'buscar': buscar}

    resultado = await ConsultarPacientes(Repo()).ejecutar('  Sol   Prueba ', 2, 20)
    assert resultado['buscar'] == 'Sol Prueba'
    assert resultado['pagina'] == 2


@pytest.mark.asyncio
async def test_no_lista_historial_de_paciente_inexistente():
    class Repo:
        async def obtener_paciente(self, paciente_id):
            return None

        async def listar_historial(self, *args):
            pytest.fail('No consultar sin paciente')

    assert await ConsultarHistorial(Repo()).ejecutar(900, 1, 20) is None


@pytest.mark.asyncio
async def test_detalle_legado_sin_json_es_legible(monkeypatch):
    class DB:
        async def execute(self, statement, params):
            assert params == {'id': 3}
            return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: {
                'id': 3, 'paciente_id': 1, 'medico_id': 2, 'especialidad_id': 1,
                'medico_nombre': 'Doctor ficticio', 'fecha_hora_inicio': '2026-01-01',
                'estado': 'anulada', 'motivo_consulta': 'Control', 'datos_clinicos_jsonb': None,
            }))

    detalle = await SqlAlchemyConsultaRepository(DB()).obtener_consulta(3)
    assert detalle['estado'] == 'anulada'
    assert detalle['diagnostico_principal'] is None
    assert 'datos_clinicos_jsonb' not in detalle


def test_json_clinico_no_sustituye_identidad_estado_ni_autor():
    detalle = presentar_consulta({
        'id': 9, 'paciente_id': 1, 'estado': 'anulada', 'medico_nombre': 'Original',
        'datos_clinicos_jsonb': {'id': 10, 'paciente_id': 2, 'estado': 'cerrada',
                                'medico_nombre': 'Otro', 'diagnostico_principal': 'Manual'},
    })
    assert (detalle['id'], detalle['paciente_id'], detalle['estado'], detalle['medico_nombre']) == (9, 1, 'anulada', 'Original')
    assert detalle['diagnostico_principal'] == 'Manual'


def test_detalle_incluye_identidad_del_paciente_aunque_este_inactivo():
    detalle = presentar_consulta({
        'id': 9, 'paciente_id': 1, 'estado': 'anulada', 'datos_clinicos_jsonb': None,
        'paciente_nombre': 'Paciente Ficticio', 'paciente_estado': 'inactivo',
        'paciente_codigo': 'PAC-TEST', 'paciente_sexo': 'F',
    })
    assert detalle['paciente']['nombre_completo'] == 'Paciente Ficticio'
    assert detalle['paciente']['estado'] == 'inactivo'
