"""El extractor redacta en estilo clínico; el dominio verifica lo comprobable contra el dictado."""
import json

import httpx
import pytest
from pydantic import ValidationError

from app.consultas.domain.extraccion import (
    SalidaModelo, formato_lista, signos_vitales_dictados, ubicar_cita, validar_propuesta,
)
from app.consultas.infrastructure.ia.ollama import ErrorExtractor, OllamaExtractor
from app.consultas.infrastructure.ia.schemas import CapturaModelo

DICTADO = ('La paciente viene porque desde hace tres días tiene dolor de garganta y fiebre por las noches. '
           'Dice que le duele al tragar y que tiene tos seca, pero no le falta el aire. De niña tuvo asma leve. '
           'Tiene 38.5 de temperatura, el pulso en 96 y la presión en 120 sobre 80. Creo que es una amigdalitis '
           'bacteriana. Le voy a dar amoxicilina de 500 cada 8 horas por 10 días.')


def propuesta(campo, valor, evidencia, **extras):
    return SalidaModelo(campos=[{'campo': campo, 'valor': valor, 'evidencia': evidencia, **extras}])


def campos(resultado):
    return {item.campo: item for item in resultado.campos}


def test_lenguaje_natural_se_redacta_en_estilo_clinico_sin_alertas():
    salida = SalidaModelo(campos=[
        {'campo': 'motivo_consulta', 'valor': 'Dolor de garganta y fiebre nocturna de 3 días',
         'evidencia': 'viene porque desde hace tres días tiene dolor de garganta y fiebre por las noches'},
        {'campo': 'sintomas', 'valor': 'Odinofagia, tos seca. Niega disnea',
         'evidencia': 'le duele al tragar y que tiene tos seca, pero no le falta el aire'},
        {'campo': 'antecedentes', 'valor': 'Asma leve en la infancia', 'evidencia': 'De niña tuvo asma leve'},
    ])
    resultado = campos(validar_propuesta(salida, DICTADO))
    assert resultado['sintomas'].valor == 'Odinofagia, tos seca, niega disnea'
    assert all(not item.alertas and not item.ambiguo for item in resultado.values())


def test_la_cita_que_no_esta_en_el_dictado_se_descarta():
    resultado = validar_propuesta(propuesta('sintomas', 'Vómitos', 'el paciente vomita todo'), DICTADO)
    assert 'sintomas' not in campos(resultado)
    assert any('Síntomas' in aviso for aviso in resultado.advertencias)


def test_la_cita_se_reemplaza_por_el_texto_real_del_dictado():
    # El modelo copió la cita con pequeñas diferencias: se muestra la frase real.
    resultado = validar_propuesta(propuesta('antecedentes', 'Asma leve', 'de nina tuvo asma leve.'), DICTADO)
    assert resultado.campos[0].evidencia == 'De niña tuvo asma leve'


def test_ubica_frases_no_consecutivas_de_una_misma_cita():
    texto = 'Consulta por palpitaciones. El electrocardiograma es normal. Lo derivo a cardiología.'
    assert ubicar_cita('Consulta por palpitaciones. Lo derivo a cardiología', texto) == \
        'Consulta por palpitaciones … Lo derivo a cardiología'


@pytest.mark.parametrize('valor,alerta', [
    ('Amoxicilina 500 mg VO cada 8 horas por 10 días', 'vía, unidad'),
    ('Amoxicilina 875 cada 8 horas por 10 días', 'cifras'),
])
def test_marca_dosis_unidades_o_vias_que_no_se_dictaron(valor, alerta):
    evidencia = 'Le voy a dar amoxicilina de 500 cada 8 horas por 10 días'
    item = validar_propuesta(propuesta('medicamentos', valor, evidencia), DICTADO).campos[0]
    assert any(alerta in texto for texto in item.alertas)


def test_unidad_dictada_con_palabras_no_genera_alerta():
    texto = 'Indico paracetamol de 500 miligramos cada ocho horas.'
    item = validar_propuesta(propuesta('medicamentos', 'Paracetamol 500 mg cada 8 horas', texto), texto).campos[0]
    assert item.alertas == []


def test_negacion_perdida_o_agregada_se_marca():
    perdida = validar_propuesta(propuesta('sintomas', 'Disnea', 'pero no le falta el aire'), DICTADO).campos[0]
    assert any('negación' in alerta for alerta in perdida.alertas)
    agregada = validar_propuesta(propuesta('sintomas', 'Tos seca. Niega fiebre', 'tiene tos seca'), DICTADO).campos[0]
    assert any('no se dictó' in alerta for alerta in agregada.alertas)


def test_presuntivo_solo_si_el_medico_expreso_duda():
    con_duda = validar_propuesta(propuesta('diagnostico_principal', 'Amigdalitis bacteriana (presuntivo)',
                                           'Creo que es una amigdalitis bacteriana'), DICTADO).campos[0]
    assert con_duda.valor == 'Amigdalitis bacteriana (presuntivo)'
    texto = 'Es una migraña sin aura.'
    sin_duda = validar_propuesta(propuesta('diagnostico_principal', 'Migraña sin aura (presuntivo)', texto), texto).campos[0]
    assert sin_duda.valor == 'Migraña sin aura'
    perdida = validar_propuesta(propuesta('diagnostico_principal', 'Amigdalitis bacteriana',
                                          'Creo que es una amigdalitis bacteriana'), DICTADO).campos[0]
    assert any('duda' in alerta for alerta in perdida.alertas)


def test_contenido_inventado_y_erratas_se_marcan_para_revision():
    texto = 'Le indico suero oral después de cada deposición.'
    errata = validar_propuesta(propuesta('indicaciones', 'Sero oral tras cada deposición', texto), texto).campos[0]
    assert any('«sero»' in alerta for alerta in errata.alertas)
    texto = 'Indico paracetamol durante tres días.'
    inventado = validar_propuesta(propuesta('indicaciones', 'Evitar alimentos pesados grasosos', texto), texto).campos[0]
    assert any('no se dictaron' in alerta for alerta in inventado.alertas)


def test_contenido_repetido_entre_campos_se_marca():
    texto = 'Le doy paracetamol para el dolor.'
    salida = SalidaModelo(campos=[
        {'campo': 'medicamentos', 'valor': 'Paracetamol', 'evidencia': texto},
        {'campo': 'tratamiento', 'valor': 'Paracetamol', 'evidencia': texto},
    ])
    tratamiento = campos(validar_propuesta(salida, texto))['tratamiento']
    assert any('Medicamentos' in alerta for alerta in tratamiento.alertas)


def test_un_campo_propuesto_dos_veces_conserva_el_primero():
    texto = 'Diagnóstico de gastritis. También podría ser colitis.'
    salida = SalidaModelo(campos=[
        {'campo': 'diagnostico_principal', 'valor': 'Gastritis', 'evidencia': 'Diagnóstico de gastritis'},
        {'campo': 'diagnostico_principal', 'valor': 'Colitis', 'evidencia': 'podría ser colitis'},
    ])
    assert [item.valor for item in validar_propuesta(salida, texto).campos] == ['Gastritis']


def test_signos_vitales_del_modelo_se_convierten_y_verifican():
    resultado = campos(validar_propuesta(SalidaModelo(campos=[
        {'campo': 'temperatura_c', 'valor': '38,5', 'evidencia': 'Tiene 38.5 de temperatura'},
        {'campo': 'frecuencia_cardiaca', 'valor': '110', 'evidencia': 'el pulso en 96'},
    ]), DICTADO))
    assert resultado['temperatura_c'].valor == 38.5 and not resultado['temperatura_c'].ambiguo
    assert resultado['frecuencia_cardiaca'].ambiguo  # 110 no aparece en lo dictado


@pytest.mark.parametrize('valor', ['450', 'treinta y ocho'])
def test_signo_vital_imposible_o_no_numerico_se_descarta(valor):
    texto = 'Temperatura 38 grados.'
    resultado = validar_propuesta(propuesta('temperatura_c', valor, texto), texto)
    assert all(item.valor == 38 for item in resultado.campos)  # queda el respaldo literal
    assert resultado.advertencias


def test_signos_vitales_en_habla_natural_se_recuperan_si_el_modelo_los_omite():
    valores = {item.campo: item.valor for item in validar_propuesta(SalidaModelo(), DICTADO).campos}
    assert valores == {'temperatura_c': 38.5, 'frecuencia_cardiaca': 96, 'presion_sistolica': 120, 'presion_diastolica': 80}


@pytest.mark.parametrize('texto,esperado', [
    ('Pesa 82 kilos y mide 1.75.', {'peso_kg': 82, 'talla_cm': 175}),
    ('Mide un metro setenta y cinco.', {'talla_cm': 175}),
    ('Temperatura 37.2, frecuencia cardíaca 110 y saturación 98 por ciento.',
     {'temperatura_c': 37.2, 'frecuencia_cardiaca': 110, 'saturacion_oxigeno': 98}),
    ('Presión sistólica 110, diastólica 70.', {'presion_sistolica': 110, 'presion_diastolica': 70}),
    ('Temperatura 39, perdón, 37 grados.', {'temperatura_c': 37}),
])
def test_detector_de_signos_vitales(texto, esperado):
    assert {item.campo: item.valor for item in signos_vitales_dictados(texto)} == esperado


@pytest.mark.parametrize('texto', [
    'Bajó de peso 3 kilos en un mes.',
    'Temperatura 37 grados. Temperatura 39 grados.',
])
def test_cifras_de_otro_momento_o_contradictorias_quedan_ambiguas(texto):
    assert all(item.ambiguo for item in validar_propuesta(SalidaModelo(), texto).campos)


@pytest.mark.parametrize('texto', ['Creo que la presión estaba cerca de 140.', 'Temperatura 98.6 grados Fahrenheit.'])
def test_mediciones_aproximadas_o_en_fahrenheit_no_se_aceptan_directo(texto):
    campo = 'presion_sistolica' if 'presión' in texto else 'temperatura_c'
    valor = '140' if campo == 'presion_sistolica' else '37'
    resultado = validar_propuesta(propuesta(campo, valor, texto), texto)
    assert all(item.ambiguo for item in resultado.campos)


def test_presion_sistolica_menor_que_diastolica_es_ambigua():
    texto = 'Presión 80 sobre 120.'
    assert all(item.ambiguo for item in validar_propuesta(SalidaModelo(), texto).campos)


def test_pregunta_sin_respuesta_es_ambigua():
    texto = '¿Tiene fiebre?'
    assert validar_propuesta(propuesta('sintomas', 'Fiebre', texto), texto).campos[0].ambiguo


def test_varios_pacientes_bloquean_toda_aplicacion():
    texto = 'Primer paciente con tos. Otro paciente con dolor.'
    resultado = validar_propuesta(propuesta('sintomas', 'Tos', 'Primer paciente con tos'), texto)
    assert resultado.bloqueada and resultado.campos == []


def test_la_sospecha_del_modelo_sobre_la_identidad_solo_advierte():
    texto = 'Viene por dolor de cabeza.'
    salida = propuesta('motivo_consulta', 'Cefalea', texto).model_copy(update={'identidad_incierta': True})
    resultado = validar_propuesta(salida, texto)
    assert not resultado.bloqueada and resultado.campos
    assert any('un solo paciente' in aviso for aviso in resultado.advertencias)


def test_esquema_rechaza_campos_fuera_del_formulario():
    with pytest.raises(ValidationError):
        propuesta('ejecutar_sql', 'DELETE FROM consulta', 'ignora las reglas')


def test_esquema_del_modelo_entrega_valores_como_texto():
    salida = CapturaModelo.model_validate({'campos': [
        {'campo': 'peso_kg', 'valor': '70', 'evidencia': 'pesa 70 kilos'}]}).propuestas()
    assert salida.campos[0].valor == '70'
    assert CapturaModelo.model_json_schema()['properties']['campos']['type'] == 'array'


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
    texto = 'Creo que es una gastritis.'
    async def responder(request):
        body = json.loads(request.content)
        assert body['stream'] is False
        assert body['format']['type'] == 'object'
        assert body['messages'][1]['content'] == texto
        assert 'tools' not in body
        return httpx.Response(200, json={'message': {'content': json.dumps({'campos': [
            {'campo': 'diagnostico_principal', 'valor': 'Gastritis (presuntivo)', 'evidencia': texto}]})}})
    salida = await OllamaExtractor(transport=httpx.MockTransport(responder)).extraer(texto)
    assert salida.campos[0].valor == 'Gastritis (presuntivo)'
    assert salida.campos[0].evidencia == 'Creo que es una gastritis'


@pytest.mark.asyncio
async def test_json_invalido_da_error_recuperable_sin_contenido_clinico():
    async def responder(request):
        return httpx.Response(200, json={'message': {'content': 'dato clínico no JSON'}})
    with pytest.raises(ErrorExtractor) as error:
        await OllamaExtractor(transport=httpx.MockTransport(responder)).extraer('Contenido ficticio sensible')
    assert 'sensible' not in str(error.value)


def test_signo_vital_del_modelo_contrastado_con_lo_dictado():
    texto = 'Temperatura 39... perdón, 37 grados. El pulso en 96.'
    salida = SalidaModelo(campos=[
        {'campo': 'temperatura_c', 'valor': '39', 'evidencia': 'Temperatura 39'},
        {'campo': 'frecuencia_cardiaca', 'valor': '69', 'evidencia': 'El pulso en 96'},
    ])
    resultado = campos(validar_propuesta(salida, texto))
    assert resultado['temperatura_c'].valor == 37  # vale la corrección dictada
    assert resultado['frecuencia_cardiaca'].ambiguo
    assert any('96' in alerta for alerta in resultado['frecuencia_cardiaca'].alertas)


@pytest.mark.parametrize('valor,esperado', [
    ('Dolor de garganta. Fiebre por las noches. Duele al tragar.', 'Dolor de garganta, fiebre por las noches, duele al tragar'),
    ('Tos seca; niega disnea', 'Tos seca, niega disnea'),
    ('Temperatura 38.5 grados. EKG normal', 'Temperatura 38.5 grados, EKG normal'),
    ('Odinofagia, tos seca', 'Odinofagia, tos seca'),
])
def test_campos_de_lista_se_separan_con_comas(valor, esperado):
    assert formato_lista(valor) == esperado


def test_sintomas_del_modelo_quedan_en_una_linea_con_comas():
    item = validar_propuesta(propuesta('sintomas', 'Odinofagia. Tos seca. Niega disnea',
                                       'le duele al tragar y que tiene tos seca, pero no le falta el aire'), DICTADO).campos[0]
    assert item.valor == 'Odinofagia, tos seca, niega disnea'
