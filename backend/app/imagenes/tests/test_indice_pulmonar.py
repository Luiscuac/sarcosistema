import math

from app.imagenes.domain.vision import TARGETS
from app.imagenes.infrastructure.vision.indice import calcular_indice, cargar_indice


def test_artefacto_versionado_coincide_con_las_18_etiquetas_del_modelo():
    a = cargar_indice()
    assert a['etiquetas'] == list(TARGETS)
    assert a['version'] == 'indice-pulmonar-v1'
    assert 'diagnóstico' in a['uso'] and a['umbrales_provisionales']['media'] < a['umbrales_provisionales']['alta']


def test_indice_reproduce_la_logistica_y_explica_contribuciones():
    a = {'version': 'prueba', 'etiquetas': ['A', 'B', 'C'], 'coeficientes': [2.0, -1.0, 0.5],
         'intercepto': -0.5, 'media': [0.5, 0.5, 0.5], 'desviacion': [0.1, 0.1, 0.1]}
    r = calcular_indice({'A': 0.7, 'B': 0.4, 'C': 0.5}, a)
    logit = -0.5 + 2.0 * 2 + -1.0 * -1 + 0
    assert math.isclose(r['valor'], 1 / (1 + math.exp(-logit)))
    assert [c['name'] for c in r['contribuciones']] == ['A', 'B']  # solo aportes positivos, ordenados
    assert 'no es diagnóstico' in r['advertencia']


def test_indice_real_queda_en_rango_y_ordena():
    bajo = calcular_indice({k: 0.1 for k in TARGETS})
    alto = calcular_indice({k: 0.9 for k in TARGETS})
    assert 0 <= bajo['valor'] <= 1 and 0 <= alto['valor'] <= 1
    assert alto['valor'] > bajo['valor']
