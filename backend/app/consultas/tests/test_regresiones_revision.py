import httpx
import pytest

from app.consultas.domain.extraccion import SalidaModelo, validar_propuesta
from app.consultas.application.ports.extractor_clinico import ErrorExtractor
from app.consultas.infrastructure.ia.ollama import OllamaExtractor
from app.consultas.infrastructure.persistence.repository import presentar_consulta


def test_negar_fiebre_no_hace_ambiguo_un_peso_y_temperatura_explicitos():
    texto = 'El paciente niega fiebre y vómitos, temperatura 36.5 grados, peso 75 kilos.'
    resultado = validar_propuesta(SalidaModelo(), texto)
    campos = {item.campo: item for item in resultado.campos}
    assert campos['temperatura_c'].valor == 36.5
    assert campos['peso_kg'].valor == 75
    assert not campos['temperatura_c'].ambiguo
    assert not campos['peso_kg'].ambiguo


def test_correccion_de_temperatura_no_modifica_peso_de_la_misma_frase():
    texto = 'Peso 75 kilos y temperatura 39, perdón, 37 grados.'
    resultado = validar_propuesta(SalidaModelo(), texto)
    assert all(item.campo != 'peso_kg' or item.valor != 37 for item in resultado.campos)


def test_no_guarda_fahrenheit_como_celsius():
    resultado = validar_propuesta(SalidaModelo(), 'Temperatura 98.6 grados Fahrenheit.')
    assert all(item.campo != 'temperatura_c' or item.ambiguo for item in resultado.campos)


@pytest.mark.asyncio
@pytest.mark.parametrize('respuesta', [{'message': {'content': None}}, {'message': {'content': []}}, []])
async def test_respuesta_malformada_del_proveedor_no_produce_error_500(respuesta):
    async def responder(request):
        return httpx.Response(200, json=respuesta)
    extractor = OllamaExtractor(transport=httpx.MockTransport(responder))
    with pytest.raises(ErrorExtractor, match='validarse'):
        await extractor.extraer('Control ficticio')


@pytest.mark.parametrize('clinicos', [[{'campo': 'sintomas'}], 'no-es-json', 17])
def test_consulta_historica_con_json_incompatible_no_rompe_el_historial(clinicos):
    resultado = presentar_consulta({'id': 9, 'paciente_id': 1, 'estado': 'cerrada', 'datos_clinicos_jsonb': clinicos})
    assert resultado['id'] == 9
    assert resultado['estado'] == 'cerrada'
    assert resultado['datos_clinicos_incompatibles'] is True
