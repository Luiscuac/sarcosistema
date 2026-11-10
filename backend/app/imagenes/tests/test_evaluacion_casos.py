from collections import Counter
from copy import deepcopy
import pytest


def test_corpus_300_equilibrado_y_reproducible():
    from scripts.evaluacion_radiologia.casos import generar_casos, validar_casos
    casos = generar_casos()
    validar_casos(casos)
    assert casos == generar_casos()
    assert len(casos) == 300
    assert len({c['informe'] for c in casos}) == 300
    assert Counter(c['grupo'] for c in casos) == dict.fromkeys(
        ['positivo', 'negativo', 'ambiguo', 'contradictorio'], 75)
    assert set(Counter((c['grupo'], c['objetivo']) for c in casos).values()) == {25}
    assert all(c['synthetic'] is True and 'SINTÉTICO' in c['etiqueta'] for c in casos)
    assert all(set(c['referencia']) == {'Consolidation', 'Effusion', 'Cardiomegaly'} for c in casos)
    textos = {c['informe'] for c in casos}
    assert 'Derrame pleural no evidente.' in textos
    assert 'Consolidación?' in textos
    assert 'No hay derrame pleural y hay cardiomegalia.' in textos


def test_validador_no_acepta_duplicados_o_etiquetas_ausentes():
    from scripts.evaluacion_radiologia.casos import generar_casos, validar_casos
    casos = generar_casos()
    casos[1] = deepcopy(casos[0])
    with pytest.raises(ValueError):
        validar_casos(casos)
