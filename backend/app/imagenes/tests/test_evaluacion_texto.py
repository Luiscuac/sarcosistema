def test_evaluacion_mide_errores_reales_sin_ocultarlos(monkeypatch):
    from scripts.evaluacion_radiologia.casos import generar_casos
    from scripts.evaluacion_radiologia import texto
    r = texto.evaluar_textos(generar_casos())
    assert r['n_casos'] == 300 and r['todas_etiquetas']['n_evaluable'] == 900
    assert r['objetivo']['n_evaluable'] == 300
    # Error documentado del extractor v1 ('Consolidación?' se leía como descrito), corregido en v2.
    caso = next(e for e in r['casos'] if e['informe'] == 'Consolidación?')
    assert caso['referencia']['Consolidation'] == caso['prediccion']['Consolidation'] == 'incierto'
    assert r['control_scores_sinteticos']['n'] == 300
    assert r['control_scores_sinteticos']['diagnosticos_confirmados'] == 0
    # La evaluación no oculta errores: un extractor que siempre afirma debe fallar casos.
    monkeypatch.setattr(texto, 'extraer_informe',
                        lambda informe, categorias: {k: {'estado': 'descrito', 'evidencia': []} for k in categorias})
    assert texto.evaluar_textos(generar_casos())['objetivo']['exactitud'] < 0.5
