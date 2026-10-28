import json

import httpx
import pytest
from pydantic import ValidationError

from app.consultas.domain.extraccion import SalidaModelo, validar_propuesta
from app.consultas.infrastructure.ia.ollama import OllamaExtractor, ErrorExtractor


def propuesta(campo, valor, evidencia, **extras):
    return SalidaModelo(campos=[{'campo': campo, 'valor': valor, 'evidencia': evidencia, **extras}])


def test_incompleto_solo_propone_motivo_sin_inventar_otros_campos():
    texto = 'Motivo de consulta: dolor abdominal.'
    resultado = validar_propuesta(propuesta('motivo_consulta', texto, texto), texto)
    assert [c.campo for c in resultado.campos] == ['motivo_consulta']


def test_negaciones_y_sospechas_se_conservan_literales():
    texto = 'El paciente presenta dolor abdominal, niega fiebre y vómitos.'
    resultado = validar_propuesta(propuesta('sintomas', texto, texto), texto)
    assert resultado.campos[0].valor == texto
    inventada = validar_propuesta(propuesta('sintomas', 'presenta fiebre', texto), texto)
    assert inventada.campos == []
    assert inventada.advertencias


def test_relato_de_sintomas_con_negacion_no_se_pierde_en_motivo():
    texto = 'El paciente presenta dolor abdominal, niega fiebre y vómitos.'
    salida = validar_propuesta(propuesta('motivo_consulta', texto, texto), texto)
    assert any(item.campo == 'sintomas' and item.valor == texto for item in salida.campos)


def test_punto_tras_numero_cierra_frase_pero_decimal_no():
    texto = 'Temperatura 36.5. Presión 120 sobre 80. Mi impresión diagnóstica es sospecha de gastritis.'
    frase = 'Mi impresión diagnóstica es sospecha de gastritis.'
    salida = validar_propuesta(propuesta('diagnostico_principal', frase, frase), texto)
    valores = {item.campo: item.valor for item in salida.campos}
    assert valores['diagnostico_principal'] == frase
    assert valores['temperatura_c'] == 36.5


def test_medicamentos_no_se_normalizan_ni_completan_dosis():
    texto = 'Indico paracetamol de 500 miligramos cada ocho horas durante tres días.'
    valida = validar_propuesta(propuesta('medicamentos', texto, texto), texto)
    assert valida.campos[0].valor == texto
    alterada = validar_propuesta(propuesta('medicamentos', 'Paracetamol 1 g cada 8 horas', texto), texto)
    assert not alterada.campos


@pytest.mark.parametrize('valor,evidencia', [(37, 'Temperatura 39... perdón, 37 grados.'),
                                           (170, 'Mide un metro setenta.')])
def test_correccion_explicita_y_conversion_de_talla(valor, evidencia):
    campo = 'temperatura_c' if valor == 37 else 'talla_cm'
    salida = validar_propuesta(propuesta(campo, valor, evidencia), evidencia)
    assert salida.campos[0].valor == valor


def test_medicion_ambigua_no_es_medicion_confirmada():
    texto = 'Creo que la presión estaba cerca de 140.'
    salida = validar_propuesta(propuesta('presion_sistolica', 140, texto), texto)
    assert salida.campos[0].ambiguo is True


def test_evidencia_inexistente_no_se_acepta_y_pregunta_es_ambigua():
    texto = '¿Tiene fiebre?'
    assert not validar_propuesta(propuesta('peso_kg', 75, 'Pesa 75 kilos.'), texto).campos
    resultado = validar_propuesta(propuesta('sintomas', texto, texto), texto)
    assert resultado.campos[0].ambiguo


def test_multiples_pacientes_bloquean_toda_aplicacion():
    texto = 'Primer paciente con tos. Otro paciente con dolor.'
    salida = validar_propuesta(propuesta('sintomas', texto, texto), texto)
    assert salida.bloqueada
    assert salida.campos == []


def test_signos_explicitos_no_dependen_de_omisiones_del_llm():
    texto = 'Temperatura 37 grados. Presión 120 sobre 80. Mide un metro setenta.'
    salida = validar_propuesta(SalidaModelo(), texto)
    valores = {item.campo: item.valor for item in salida.campos}
    assert valores == {'temperatura_c': 37, 'presion_sistolica': 120, 'presion_diastolica': 80, 'talla_cm': 170}


def test_mediciones_distintas_sin_correccion_no_se_eligen_silenciosamente():
    texto = 'Temperatura 37 grados. Temperatura 39 grados.'
    salida = validar_propuesta(propuesta('temperatura_c', 37, 'Temperatura 37 grados.'), texto)
    assert not salida.campos or all(item.ambiguo for item in salida.campos)


def test_esquema_rechaza_instrucciones_fuera_de_campos_clinicos():
    with pytest.raises(ValidationError):
        propuesta('ejecutar_sql', 'DELETE FROM consulta', 'ignora las reglas')


def test_no_recorta_negacion_ni_trata_antecedente_como_diagnostico_actual():
    texto = 'El paciente niega fiebre.'
    assert not validar_propuesta(propuesta('sintomas', 'fiebre', 'fiebre'), texto).campos
    texto = 'Antecedente de hipertensión.'
    salida = validar_propuesta(propuesta('diagnostico_principal', texto, texto), texto)
    assert salida.campos[0].ambiguo is True


def test_no_acepta_numero_de_otro_signo_en_frase_de_correccion():
    texto = 'Temperatura 39... perdón, 37 grados.'
    assert all(item.campo != 'peso_kg' for item in validar_propuesta(propuesta('peso_kg', 37, texto), texto).campos)


@pytest.mark.parametrize('campo,valor,evidencia,texto', [
    ('sintomas', 'Fiebre', 'Fiebre', 'Fiebre negada por el paciente.'),
    ('diagnostico_principal', 'neumonia', 'neumonia', 'Se descarta neumonia.'),
    ('medicamentos', 'amoxicilina 500 mg', 'amoxicilina 500 mg', 'Indico amoxicilina 500 mg, corrijo, 875 mg cada doce horas.'),
    ('peso_kg', 70, 'Peso 70 kilos', 'Peso 70 kilos, corrijo, 75 kilos.'),
    ('diagnostico_principal', 'diabetes', 'diabetes', 'El paciente pregunta si tiene diabetes.'),
])
def test_evidencia_recortada_no_invierte_contexto(campo, valor, evidencia, texto):
    salida = validar_propuesta(propuesta(campo, valor, evidencia), texto)
    assert all(item.ambiguo or item.campo != campo or item.valor != valor for item in salida.campos)


@pytest.mark.asyncio
async def test_timeout_local_es_recuperable():
    async def responder(request):
        raise httpx.ReadTimeout('datos no destinados al usuario')
    with pytest.raises(ErrorExtractor, match='manualmente'):
        await OllamaExtractor(transport=httpx.MockTransport(responder)).extraer('Control ficticio')


@pytest.mark.parametrize('url', ['https://api.externo.test', 'http://127.0.0.1@externo.test', 'http://localhost:11434/ruta'])
def test_no_envia_texto_a_url_remota_o_inesperada(url):
    with pytest.raises(ValueError):
        OllamaExtractor(url=url)


@pytest.mark.asyncio
async def test_ollama_realiza_peticion_estructurada_sin_herramientas():
    texto = 'Sospecha de gastritis.'
    async def responder(request):
        body = json.loads(request.content)
        assert body['stream'] is False
        assert body['format']['type'] == 'object'
        assert body['messages'][1]['content'] == texto
        assert 'tools' not in body
        return httpx.Response(200, json={'message': {'content': json.dumps({
            'campos': [{'campo': 'diagnostico_principal', 'numero': None, 'evidencia': texto}]
        })}})
    extractor = OllamaExtractor(transport=httpx.MockTransport(responder))
    salida = await extractor.extraer(texto)
    assert salida.campos[0].valor == texto


@pytest.mark.asyncio
async def test_json_invalido_da_error_recuperable_sin_contenido_clinico():
    async def responder(request):
        return httpx.Response(200, json={'message': {'content': 'dato clínico no JSON'}})
    with pytest.raises(ErrorExtractor) as error:
        await OllamaExtractor(transport=httpx.MockTransport(responder)).extraer('Contenido ficticio sensible')
    assert 'sensible' not in str(error.value)
