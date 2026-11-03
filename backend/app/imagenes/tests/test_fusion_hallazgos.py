from app.imagenes.application.fusionar_hallazgos import extraer_informe, fusionar


def test_negacion_e_incertidumbre_con_evidencia_literal():
    texto = 'No se observa derrame pleural. Posible consolidación basal derecha. Cardiomegalia.'
    datos = extraer_informe(texto)
    assert datos['Effusion']['estado'] == 'negado'
    assert datos['Consolidation']['estado'] == 'incierto'
    assert datos['Cardiomegaly']['estado'] == 'descrito'
    assert 'basal derecha' in datos['Consolidation']['evidencia'][0]
    assert datos['Effusion']['evidencia'][0] in texto


def test_no_descartar_no_es_negacion_ni_confirmacion():
    assert extraer_informe('No se descarta derrame pleural.')['Effusion']['estado'] == 'incierto'
    assert extraer_informe('No se observa derrame; hay consolidación.')['Consolidation']['estado'] == 'descrito'


def test_contradiccion_interna_no_se_resuelve():
    r = extraer_informe('Derrame pleural. No se observa derrame pleural.')
    assert r['Effusion']['estado'] == 'ambiguo'


def test_score_alto_y_negacion_solo_sugiere_revision():
    visual = {'findings':[{'name':'Effusion','score':0.8}], 'experimental':True}
    r = fusionar(visual, 'No se observa derrame pleural.')
    assert len(r['discrepancias']) == 1
    assert r['hallazgos_confirmados'] == []
    assert r['criterio_tecnico']['umbral'] == 0.5
    assert 'no clínico' in r['criterio_tecnico']['descripcion']
    assert r['informe_original'] == 'No se observa derrame pleural.'


def test_score_bajo_no_descarta_enfermedad_ni_declara_normal():
    r = fusionar({'findings':[{'name':'Effusion','score':0.1}]}, '')
    assert r['discrepancias'] == []
    assert r['informe']['Effusion']['estado'] == 'no_mencionado'
    assert r['hallazgos_confirmados'] == []
