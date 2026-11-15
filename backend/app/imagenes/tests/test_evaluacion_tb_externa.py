"""Evaluación externa TB: lectura de metadatos, conversión de paleta e índice NLM (sin red ni pesos)."""
import pytest


def test_lectura_clinica_formatos_shenzhen_y_montgomery():
    from scripts.evaluacion_radiologia.tb_externa import lectura_clinica
    sz = lectura_clinica('female 28yrs  \nright upper PTB with fibrous changes')
    assert sz['edad'] == 28 and sz['sexo'] == 'female' and 'PTB' in sz['lectura']
    mc = lectura_clinica("Patient's Sex: M \nPatient's Age: 059Y\ninactive TB scars")
    assert mc['edad'] == 59 and mc['sexo'] == 'male'
    ninio = lectura_clinica('male 8month normal')
    assert ninio['edad'] == pytest.approx(8 / 12)
    assert lectura_clinica('') == {'edad': None, 'sexo': None, 'lectura': ''}


def test_evaluacion_usa_el_preprocesamiento_de_produccion():
    # Regresión: Shenzhen viene en modo "P"; tratarlo como 16 bits invirtió los resultados.
    import inspect
    from scripts.evaluacion_radiologia import tb_externa
    assert 'preparar_imagen' in inspect.getsource(tb_externa.preparar)
    assert not hasattr(tb_externa, 'a_arreglo')


def test_metricas_detecta_separacion_y_no_evalua_una_sola_clase():
    from scripts.evaluacion_radiologia.tb_externa import metricas, PULMONARES
    fila = lambda tb, s: {'tb': tb, 'scores': {k: s for k in PULMONARES}}
    r = metricas([fila(1, .9), fila(1, .8), fila(0, .2), fila(0, .1)], PULMONARES)
    assert r['max_pulmonar']['auroc'] == 1.0
    assert metricas([fila(1, .9)], PULMONARES)['por_categoria'] == {}


def test_parsear_indice_nlm():
    from scripts.preparar_tb_nlm import parsear_indice
    html = ("<tr><td class='link'><a href='CXR_png/'>CXR_png/</a></td><td class='size'>-</td></tr>"
            "<tr><td class='link'><a href='CHNCXR_0001_0.png'>CHNCXR_0001_0.png</a></td><td class='size'>5920202</td></tr>")
    assert parsear_indice(html) == [('CHNCXR_0001_0.png', 5920202)]


def test_pointing_game_lleva_pico_del_recorte_a_la_imagen_y_compara_con_azar(tmp_path):
    from scripts.evaluacion_radiologia.tb_mapas import acierta, cargar_regiones, fraccion_azar, pico_en_imagen
    (tmp_path / 'shenzhen').mkdir()
    (tmp_path / 'shenzhen' / 'shenzhen_consensus_roi.csv').write_text(
        'patientId,x_dis,y_dis,width_dis,height_dis,Labels\nCHNCXR_0001_1.png,512,0,512,512,TB\nCHNCXR_0001_1.png,1,1,0,5,TB\n')
    regiones = cargar_regiones(tmp_path)
    assert regiones == {'CHNCXR_0001_1': [(0.5, 0.0, 0.5, 0.5)]}  # se descarta la caja de ancho 0
    region = {'x': 0.25, 'y': 0.0, 'ancho': 0.5, 'alto': 1.0}  # recorte central de una imagen apaisada
    punto = pico_en_imagen({'pico': {'x': 0.9, 'y': 0.1}}, region)
    assert punto == (0.7, 0.1) and acierta(punto, regiones['CHNCXR_0001_1'])
    assert not acierta((0.3, 0.9), regiones['CHNCXR_0001_1'])
    assert 0.2 < fraccion_azar(regiones['CHNCXR_0001_1'], region) < 0.3  # 1/4 del recorte
