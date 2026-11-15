from app.imagenes.application.fusionar_hallazgos import extraer_informe, fusionar
import pytest


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


@pytest.mark.parametrize('texto,nombre,estado', [
    ('Sin derrame pleural, con cardiomegalia.','Cardiomegaly','descrito'),
    ('No se puede descartar derrame pleural.','Effusion','incierto'),
    ('Derrame pleural dudoso.','Effusion','incierto'),
    ('No hay cambios en la cardiomegalia.','Cardiomegaly','ambiguo'),
])
def test_no_promueve_negacion_o_incertidumbre_fuera_de_alcance(texto,nombre,estado):
    assert extraer_informe(texto)[nombre]['estado'] == estado


# Frases tipo de informes radiológicos (escritas a mano, ficticias): la extracción cubre las 18 categorías.
REALISTAS = [
    ('Silueta cardíaca de tamaño normal. Senos costofrénicos libres.', {'Cardiomegaly': 'negado', 'Effusion': 'negado'}),
    ('Opacidad heterogénea en lóbulo superior derecho con imagen cavitada.', {'Lung Opacity': 'descrito', 'Lung Lesion': 'descrito'}),
    ('No se observan nódulos ni masas.', {'Nodule': 'negado', 'Mass': 'negado'}),
    ('Campos pulmonares sin infiltrados.', {'Infiltration': 'negado'}),
    ('Fractura antigua del sexto arco costal derecho.', {'Fracture': 'descrito'}),
    ('Pequeño derrame pleural izquierdo vs engrosamiento pleural.', {'Effusion': 'incierto', 'Pleural_Thickening': 'incierto'}),
    ('Mediastino centrado, de amplitud normal.', {'Enlarged Cardiomediastinum': 'negado'}),
    ('Hiperinsuflación pulmonar compatible con enfisema.', {'Emphysema': 'descrito'}),
    ('Infiltrado intersticial bilateral, a correlacionar con clínica.', {'Infiltration': 'descrito'}),
    ('Sin evidencia de neumotórax tras la colocación del catéter.', {'Pneumothorax': 'negado'}),
    ('Atelectasias laminares basales.', {'Atelectasis': 'descrito'}),
    ('Edema agudo de pulmón.', {'Edema': 'descrito'}),
    ('Engrosamiento pleural apical bilateral.', {'Pleural_Thickening': 'descrito'}),
    ('Cardiomegalia grado II con signos de redistribución vascular.', {'Cardiomegaly': 'descrito'}),
    ('No hay derrame pleural ni neumotórax.', {'Effusion': 'negado', 'Pneumothorax': 'negado'}),
    ('Imagen nodular de 8 mm en lóbulo medio, a descartar granuloma.', {'Nodule': 'descrito'}),
    ('Consolidación en lóbulo inferior izquierdo sugestiva de neumonía.', {'Consolidation': 'descrito', 'Pneumonia': 'incierto'}),
    ('Radiografía de tórax sin alteraciones significativas.', {}),
    ('Tractos fibrosos apicales en relación con secuelas de TB.', {'Fibrosis': 'descrito'}),
    ('No se descarta neumonía basal derecha.', {'Pneumonia': 'incierto'}),
    ('Sin cardiomegalia. Hernia hiatal.', {'Cardiomegaly': 'negado', 'Hernia': 'descrito'}),
    ('Right upper lobe infiltrate. No pleural effusion.', {'Infiltration': 'descrito', 'Effusion': 'negado'}),
]


@pytest.mark.parametrize('texto,esperado', REALISTAS)
def test_frases_realistas_en_18_categorias_sin_menciones_falsas(texto, esperado):
    r = extraer_informe(texto)
    assert len(r) == 18
    assert {k: v['estado'] for k, v in r.items() if v['estado'] != 'no_mencionado'} == esperado


def _todas(**scores):
    return {'all_findings': [{'name': k.replace('__', ' '), 'score': v} for k, v in scores.items()]}


def test_avisa_posible_omision_solo_con_las_18_categorias():
    visual = _todas(Nodule=0.9, Effusion=0.8, Cardiomegaly=0.1, Mass=0.6)
    r = fusionar(visual, 'No se observa derrame pleural. Masa hiliar derecha.')
    assert [d['hallazgo'] for d in r['discrepancias']] == ['Effusion']
    assert [d['hallazgo'] for d in r['coincidencias']] == ['Mass']
    assert [d['hallazgo'] for d in r['posibles_omisiones']] == ['Nodule']
    assert r['criterio_tecnico']['categorias_comparadas'] == 18
    assert r['hallazgos_confirmados'] == []
    # Resultado antiguo (3 categorías): no inventa omisiones de categorías que no evaluó.
    antiguo = fusionar({'findings': [{'name': 'Effusion', 'score': 0.8}]}, '')
    assert antiguo['posibles_omisiones'] == [] and set(antiguo['informe']) == {'Effusion'}


def test_omisiones_se_limitan_y_ordenan_por_score():
    visual = _todas(**{n: 0.7 + i / 100 for i, n in enumerate(
        ['Atelectasis', 'Consolidation', 'Infiltration', 'Pneumothorax', 'Edema', 'Emphysema', 'Fibrosis'])},
        Hernia=0.6)  # sobre el punto técnico pero bajo el umbral de omisión: no se avisa
    r = fusionar(visual, '')
    assert r['omisiones_totales'] == 7 and len(r['posibles_omisiones']) == 3
    assert 'Hernia' not in {d['hallazgo'] for d in r['posibles_omisiones']}
    assert r['posibles_omisiones'][0]['hallazgo'] == 'Fibrosis'
