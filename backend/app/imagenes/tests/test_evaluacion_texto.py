def test_evaluacion_mide_errores_reales_sin_ocultarlos():
    from scripts.evaluacion_radiologia.casos import generar_casos
    from scripts.evaluacion_radiologia.texto import evaluar_textos
    r = evaluar_textos(generar_casos())
    assert r['n_casos'] == 300 and r['todas_etiquetas']['n_evaluable'] == 900
    assert r['objetivo']['n_evaluable'] == 300
    assert r['objetivo']['exactitud'] < 1
    error = next(e for e in r['casos'] if e['informe'] == 'Consolidación?')
    assert error['referencia']['Consolidation'] == 'incierto'
    assert error['prediccion']['Consolidation'] == 'descrito'
    assert r['control_scores_sinteticos']['n'] == 300
    assert r['control_scores_sinteticos']['diagnosticos_confirmados'] == 0
