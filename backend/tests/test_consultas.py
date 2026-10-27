from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.consultas.presentation.schemas import ConsultaNueva
from app.consultas.application.use_cases.registrar_consulta import RegistrarConsulta
from app.consultas.domain.validators import buscar_normalizado


def datos(**overrides):
    return dict(paciente_id=1, clave_idempotencia=uuid4(), motivo_consulta='Dolor',
                diagnostico_principal='Evaluación manual', **overrides)


@pytest.mark.parametrize('campo,valor', [
    ('peso_kg', 0), ('temperatura_c', -1), ('saturacion_oxigeno', 101),
    ('frecuencia_cardiaca', 0), ('talla_cm', float('inf')),
])
def test_mediciones_invalidas_no_se_guardan(campo, valor):
    with pytest.raises(ValidationError):
        ConsultaNueva(**datos(**{campo: valor}))


def test_presion_sistolica_debe_superar_diastolica():
    with pytest.raises(ValidationError):
        ConsultaNueva(**datos(presion_sistolica=70, presion_diastolica=80))


def test_solo_motivo_y_diagnostico_son_obligatorios():
    consulta = ConsultaNueva(**datos())
    assert consulta.sintomas is None
    assert consulta.peso_kg is None
    assert consulta.diagnostico_principal == 'Evaluación manual'


def test_narrativa_excesiva_no_se_guarda():
    with pytest.raises(ValidationError):
        ConsultaNueva(**datos(sintomas='a' * 10001))


@pytest.mark.parametrize('texto', ['   ', '%%', '___', ' % _ '])
def test_busqueda_sin_letras_ni_numeros_no_expone_listado(texto):
    with pytest.raises(ValueError):
        buscar_normalizado(texto)


@pytest.mark.asyncio
async def test_medico_sin_especialidad_vigente_no_inserta():
    class Repositorio:
        async def medico_vigente(self, usuario_id):
            return None

        async def crear(self, *args):
            pytest.fail('No se debe guardar una consulta sin especialidad vigente')

    with pytest.raises(ValueError, match='especialidad vigente'):
        await RegistrarConsulta(Repositorio()).ejecutar(ConsultaNueva(**datos()), 7)
