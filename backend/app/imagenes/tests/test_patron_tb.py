"""Patrón de TB experimental: artefacto coherente, niveles y resumen de triaje (sin torch ni BD)."""
import pytest

from app.imagenes.application.triaje import resumir_triaje
from app.imagenes.domain.vision import TARGETS
from app.imagenes.infrastructure.vision.indice import cargar_indice
from app.imagenes.infrastructure.vision.patron_tb import calcular_patron_tb, cargar_patron


def test_artefacto_usa_las_mismas_18_salidas_que_el_indice():
    a = cargar_patron()
    assert a['version'] == 'patron-tb-v1'
    assert a['etiquetas'] == cargar_indice()['etiquetas']
    assert set(a['etiquetas']) <= set(TARGETS)
    assert 0 < a['umbrales']['compatible'] < 1
    assert 'aviso_en_sanos' in a['metricas']['tbx11k_val']


def _artefacto(coef):
    return {'version': 'prueba', 'etiquetas': ['A'], 'coeficientes': [coef], 'media': [0.5], 'desviacion': [0.1],
            'intercepto': 0.0, 'umbrales': {'compatible': 0.6}}


@pytest.mark.parametrize('score,nivel', [(0.9, 'compatible'), (0.55, 'compatible'), (0.52, None), (0.1, None)])
def test_niveles_solo_avisan_y_nunca_descartan(score, nivel):
    r = calcular_patron_tb({'A': score}, _artefacto(1.0))
    assert r['nivel'] == nivel
    assert 0 <= r['valor'] <= 1
    assert 'No descarta TB' in r['advertencia']


def test_resultado_real_con_18_scores_tiene_patron():
    from app.imagenes.infrastructure.vision.worker import resultado_enriquecido
    r = resultado_enriquecido({n: 0.3 for n in TARGETS}, list(TARGETS))
    assert r['patron_tb']['version'] == 'patron-tb-v1'
    assert r['patron_tb']['nivel'] in (None, 'compatible')


def test_triaje_conserva_el_patron_mas_fuerte_del_estudio():
    filas = [
        {'estudio_id': 1, 'estado': 'completado', 'indice': 0.8, 'calidad': 'ok', 'contribuciones': [], 'patron_tb': None},
        {'estudio_id': 1, 'estado': 'completado', 'indice': 0.4, 'calidad': 'ok', 'contribuciones': [], 'patron_tb': 'compatible'},
        {'estudio_id': 2, 'estado': 'completado', 'indice': 0.3, 'calidad': 'ok', 'contribuciones': []},
    ]
    r = resumir_triaje(filas)
    assert r[1]['patron_tb'] == 'compatible'
    assert r[2]['patron_tb'] is None
