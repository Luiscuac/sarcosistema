"""Comparación transparente informe ↔ imagen en las 18 categorías del modelo.

Extracción por reglas (no es un extractor clínico validado ni un LLM): busca términos en
español/inglés sin depender de tildes, separa cláusulas y clasifica cada mención como
descrito, negado, incierto o ambiguo. Nunca confirma diagnósticos.
"""
import re
import unicodedata

# Patrones sobre texto normalizado (minúsculas, sin tildes).
PATRONES = {
    'Atelectasis': r'\batelecta\w*|\bcolapso (?:lobar|pulmonar|segmentario|del lobulo)\b|\batelectasis\b',
    'Consolidation': r'\bconsolidaci(?:on|ones)\b|\bconsolidation\b|\bcondensaci(?:on|ones)\b',
    'Infiltration': r'\binfiltrad[oa]s?\b|\binfiltraci(?:on|ones)\b|\binfiltrat(?:e|es|ion)\b',
    'Pneumothorax': r'\bneumotorax\b|\bpneumothorax\b',
    'Edema': r'\bedema\b',
    'Emphysema': r'\benfisema\w*|\bemphysema\b|\bhiperinsuflaci(?:on)\b|\bhyperinflation\b',
    'Fibrosis': r'\bfibros(?:is|[oa]s?)\b|\bfibrotic[oa]s?\b|\bfibrotic\b|\bfibrous\b',
    'Effusion': r'\bderrame(?:s)?(?: pleural(?:es)?)?\b|\b(?:pleural )?effusions?\b|\bliquido pleural\b',
    'Pneumonia': r'\b(?:bronco)?neumonia\w*|\bpneumonia\b|\bproceso neumonico\b',
    'Pleural_Thickening': r'\bengrosamiento pleural\b|\bpaquipleuritis\b|\bpleural thickening\b',
    'Cardiomegaly': r'\bcardiomegalia\b|\bcardiomegaly\b|\bsilueta cardiaca (?:aumentada|agrandada)\b|\bagrandamiento cardiaco\b',
    'Nodule': r'\bnodul(?:o|os|ar|ares)\b|\bmicronodul\w*|\bnodules?\b',
    'Mass': r'\bmasas?\b|\bmass(?:es)?\b|\btumoraci(?:on|ones)\b',
    'Hernia': r'\bhernia\w*',
    'Lung Lesion': r'\blesi(?:on|ones) pulmonar(?:es)?\b|\bcavita\w*|\bcavern\w*|\bcavit(?:y|ies)\b|\blung lesions?\b',
    'Fracture': r'\bfractur\w*',
    'Lung Opacity': r'\bopacidad(?:es)?\b|\bopacit(?:y|ies)\b|\bvidrio esmerilado\b|\bground glass\b|\bradiopacidad(?:es)?\b',
    'Enlarged Cardiomediastinum': r'\bensanchamiento (?:del )?mediastin\w*|\bmediastino ensanchado\b|\bcardiomediastin\w*|\bwidened mediastinum\b',
}
# Frases de normalidad específicas que equivalen a una negación de la categoría.
NORMALES = {
    'Cardiomegaly': r'\bsilueta cardiaca (?:normal|conservada|de tamano normal|dentro de (?:los )?limites)|\bindice cardiotoracico (?:normal|conservado)',
    'Effusion': r'\bsenos costofrenicos (?:libres|conservados|agudos|permeables)|\bsenos costodiafragmaticos (?:libres|conservados)',
    'Enlarged Cardiomediastinum': r'\bmediastino (?:normal|conservado|centrado|de amplitud normal|sin ensanchamiento)',
}
AMBIGUO = r'\bsin cambios\b|\bno (?:hay|se observan?) cambios\b|\bsin variaci\w*|\bantecedente de\b|\bpresencia actual no determinada\b|\bunchanged\b'
# La duda tiene alcance: hacia adelante (antes del término), justo después del término o en toda la cláusula.
INCIERTO_PREVIO = (r'\bposibl\w*|\bprobabl\w*|\bsugestiv\w*|\bdudos\w*|\bsospech\w*|\bno (?:se )?(?:puede )?descart\w*'
                   r'|\bno puede descartarse\b|\ba descartar\b|\bpodria\b|\bvalorar\b|\bevaluar\b|\bvs\b|\bversus\b'
                   r'|\bpossible\b|\bsuspected\b|\bprobable\b')
INCIERTO_POSTERIOR = r'^\W*(?:\w+\W+){0,2}?(?:dudos\w*|no descartable|probable|posible|sospechos\w*|vs|versus|\?)'
INCIERTO_CLAUSULA = (r'\?|¿|\bpendiente\b|\bindeterminad\w*|\bno (?:es )?concluyente\b|\bno es posible confirmar\b'
                     r'|\bno se puede evaluar\b|\bquestionable\b')
NEGACION_PREVIA = r'\b(?:no|sin|ausencia|ni|tampoco|libre de|negativo para|se descarta|descarta|without|no evidence of)\b'
NEGACION_POSTERIOR = r'^\W*(?:\w+\W+){0,2}?(?:no evidente|ausente|ausentes|descartad[oa]s?|negativ[oa]|not seen|absent)\b'
SEPARADORES = (r'[.;,\n]+|\bpero\b|\bsin embargo\b|\bcon\b|\bwith\b'
               r'|\by\b(?=\s+(?:hay|se|existe|presenta|persiste|muestra|no|sin)\b)')


def normalizar(texto: str) -> str:
    sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return sin_tildes.lower()


def _estado_clausula(clausula: str, coincidencia: re.Match) -> str:
    if re.search(AMBIGUO, clausula):
        return 'ambiguo'
    antes, despues = clausula[:coincidencia.start()], clausula[coincidencia.end():]
    if re.search(INCIERTO_CLAUSULA, clausula) or re.search(INCIERTO_PREVIO, antes) or re.search(INCIERTO_POSTERIOR, despues):
        return 'incierto'
    if re.search(NEGACION_PREVIA, antes) or re.search(NEGACION_POSTERIOR, despues):
        return 'negado'
    return 'descrito'


def extraer_informe(texto: str, categorias=None) -> dict:
    categorias = list(categorias or PATRONES)
    originales = [c.strip() for c in re.split(SEPARADORES, texto or '', flags=re.I) if c and c.strip()]
    resultado = {}
    for nombre in categorias:
        estados, evidencia = set(), []
        for original in originales:
            clausula = normalizar(original)
            normal = NORMALES.get(nombre)
            if normal and re.search(normal, clausula):
                estados.add('negado')
                evidencia.append(original)
                continue
            coincidencia = re.search(PATRONES[nombre], clausula)
            if not coincidencia:
                continue
            evidencia.append(original)
            estados.add(_estado_clausula(clausula, coincidencia))
        resultado[nombre] = {'estado': next(iter(estados)) if len(estados) == 1 else ('ambiguo' if estados else 'no_mencionado'),
                             'evidencia': evidencia}
    return resultado


MAX_OMISIONES = 3
# Las omisiones exigen un score más alto que las discrepancias: en casos graves casi todas las
# categorías superan 0,5 y avisar de todas produce fatiga de alertas (visto en la prueba de punta a punta).
UMBRAL_OMISION = 0.7


def fusionar(visual: dict, informe: str, umbral: float = 0.5) -> dict:
    hallazgos = visual.get('all_findings') or visual.get('findings', [])
    completo = bool(visual.get('all_findings'))
    nombres = [h['name'] for h in hallazgos if h['name'] in PATRONES]
    extraido = extraer_informe(informe, PATRONES if completo else nombres)
    discrepancias, coincidencias, omisiones = [], [], []
    for hallazgo in sorted(hallazgos, key=lambda h: h['score'], reverse=True):
        nombre = hallazgo['name']
        if nombre not in extraido or hallazgo['score'] < umbral:
            continue
        estado = extraido[nombre]['estado']
        if estado == 'negado':
            discrepancias.append({'hallazgo': nombre, 'score': hallazgo['score'], 'tipo': 'discrepancia',
                'mensaje': 'El score experimental destacado y la negación del informe requieren revisión profesional. No se resuelve la discrepancia automáticamente.'})
        elif estado == 'descrito':
            coincidencias.append({'hallazgo': nombre, 'score': hallazgo['score'], 'tipo': 'coincidencia',
                'mensaje': 'El término está descrito en el informe y tiene score experimental destacado; no confirma diagnóstico.'})
        elif estado == 'no_mencionado' and completo and hallazgo['score'] >= max(umbral, UMBRAL_OMISION):
            omisiones.append({'hallazgo': nombre, 'score': hallazgo['score'], 'tipo': 'posible_omision',
                'mensaje': 'El modelo destaca esta categoría y el informe no la menciona. Revisar si corresponde describirla o descartarla.'})
    return {'experimental': True, 'informe_original': informe, 'informe': extraido,
        'discrepancias': discrepancias, 'coincidencias': coincidencias,
        'posibles_omisiones': omisiones[:MAX_OMISIONES], 'omisiones_totales': len(omisiones),
        'hallazgos_confirmados': [],
        'criterio_tecnico': {'umbral': umbral, 'umbral_omision': max(umbral, UMBRAL_OMISION), 'categorias_comparadas': len(extraido),
            'descripcion': 'Criterio técnico no clínico para destacar scores normalizados XRV; no equivale a enfermedad ni a probabilidad.'},
        'advertencias': [f'Extracción por reglas de términos explícitos en {len(extraido)} categorías; puede omitir o interpretar mal el contexto.',
                         'Un score bajo o la ausencia de mención no descarta enfermedad. Revisión médica obligatoria.']}
