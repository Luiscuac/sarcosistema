import pytest


def test_matriz_macro_f1_y_desconocidos():
    from scripts.evaluacion_radiologia.metricas import clasificacion
    r = clasificacion(['a', 'a', 'b', 'b', None], ['a', 'b', 'b', 'b', 'a'])
    assert r['n_total'] == 5 and r['n_evaluable'] == 4 and r['excluidos'] == 1
    assert r['exactitud'] == .75
    assert r['matriz']['a'] == {'a': 1, 'b': 1}
    assert r['macro_f1'] == pytest.approx((2/3 + .8)/2)
    assert clasificacion([], [])['exactitud'] is None


def test_binaria_auc_ap_empates_y_clase_ausente():
    from scripts.evaluacion_radiologia.metricas import binaria
    r = binaria([0, 1, 0, 1, None], [.1, .9, .5, .5, .8])
    assert r['auroc'] == .875
    assert r['ap'] == pytest.approx(5/6)
    assert (r['tp'], r['fp'], r['tn'], r['fn']) == (2, 1, 1, 0)
    assert binaria([1], [.7])['auroc'] is None
    assert binaria([0], [.7])['ap'] is None
    with pytest.raises(ValueError):
        binaria([1], [float('nan')])
    with pytest.raises(ValueError):
        binaria([1, 0], [.1])
