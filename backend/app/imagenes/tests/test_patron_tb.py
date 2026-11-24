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


def test_ensamble_promedia_solo_categorias_entrenadas():
    from app.imagenes.infrastructure.vision.ensamble import promediar
    base = {'A': 0.2, 'B': 0.8}
    r = promediar(base, [{'A': 0.4}, {'A': float('nan'), 'B': 0.6}, {}])
    assert r == pytest.approx({'A': 0.3, 'B': 0.7})


def test_ensamble_no_preparado_si_falta_manifiesto_o_pesos(tmp_path):
    import json
    from app.imagenes.infrastructure.vision.ensamble import MODELOS, ensamble_preparado
    assert not ensamble_preparado(tmp_path)
    (tmp_path / 'manifest.json').write_text(json.dumps({'modelos': {n: {'weights_file': f'{n}.st'} for n in MODELOS}}))
    assert not ensamble_preparado(tmp_path)
    for n in MODELOS:
        (tmp_path / f'{n}.st').write_bytes(b'x')
    assert ensamble_preparado(tmp_path)
    (tmp_path / 'manifest.json').write_text('{roto')
    assert not ensamble_preparado(tmp_path)


def test_patron_usa_v2_con_ensamble_y_v1_sin_el():
    from app.imagenes.infrastructure.vision.patron_tb import ARTEFACTO_ENSAMBLE
    from app.imagenes.infrastructure.vision.worker import resultado_enriquecido
    scores = {n: 0.3 for n in TARGETS}
    v2 = cargar_patron(str(ARTEFACTO_ENSAMBLE))
    assert v2['version'] == 'patron-tb-v2' and v2['requiere_ensamble'] and v2['etiquetas'] == cargar_indice()['etiquetas']
    con = resultado_enriquecido(scores, list(TARGETS), {n: 0.6 for n in TARGETS})
    sin = resultado_enriquecido(scores, list(TARGETS))
    assert con['patron_tb']['version'] == 'patron-tb-v2' and con['patron_tb']['ensamble'] is True
    assert sin['patron_tb']['version'] == 'patron-tb-v1' and sin['patron_tb']['ensamble'] is False
    # El índice siempre usa solo el modelo base.
    assert con['indice_pulmonar'] == sin['indice_pulmonar']


def test_corte_local_reemplaza_al_del_artefacto():
    a = _artefacto(1.0)
    assert calcular_patron_tb({'A': 0.55}, a)['nivel'] == 'compatible'
    local = calcular_patron_tb({'A': 0.55}, a, umbral=0.9)
    assert local['nivel'] is None and local['umbral'] == 0.9 and local['umbral_origen'] == 'local'


def test_config_rechaza_corte_tb_fuera_de_rango(tmp_path):
    from app.imagenes.domain.vision import VisionConfig
    assert VisionConfig(tmp_path, umbral_tb=0.7).umbral_tb == 0.7
    for malo in (0, 1, 1.5):
        with pytest.raises(ValueError):
            VisionConfig(tmp_path, umbral_tb=malo)


def test_patron_en_uso_informa_version_y_corte():
    from app.imagenes.infrastructure.vision.patron_tb import patron_en_uso
    assert patron_en_uso(False, None)['version'] == 'patron-tb-v1'
    assert patron_en_uso(False, 0.42)['umbral_actual'] == 0.42
