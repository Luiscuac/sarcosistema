"""Extracción acotada y transparente: no es un extractor clínico validado."""
import re

PATRONES = {
    'Consolidation': r'\bconsolidaci[oó]n\b|\bconsolidation\b',
    'Effusion': r'\bderrame(?:\s+pleural)?\b|\bpleural effusion\b',
    'Cardiomegaly': r'\bcardiomegalia\b|\bcardiomegaly\b',
}


def extraer_informe(texto: str) -> dict:
    resultado = {}
    clausulas = re.split(r'[.;,\n]+|\bpero\b|\bsin embargo\b|\bcon\b', texto, flags=re.I)
    for nombre, patron in PATRONES.items():
        estados, evidencia = set(), []
        for clausula in clausulas:
            if not re.search(patron, clausula, re.I):
                continue
            evidencia.append(clausula.strip())
            if re.search(r'sin cambios|no (?:hay|se observan?) cambios|sin variaci[oó]n', clausula, re.I):
                estados.add('ambiguo')
            elif re.search(r'posible|probable|sugestiv|dudos[oa]|sospech|no (?:se )?(?:puede )?descart|no puede descartarse|\bpossible\b|\bsuspected\b', clausula, re.I):
                estados.add('incierto')
            elif re.search(r'\bno\b|\bsin\b|\bausencia\b|\bwithout\b', clausula[:re.search(patron,clausula,re.I).start()], re.I):
                estados.add('negado')
            else:
                estados.add('descrito')
        resultado[nombre] = {'estado': next(iter(estados)) if len(estados)==1 else (
            'ambiguo' if estados else 'no_mencionado'), 'evidencia':evidencia}
    return resultado


def fusionar(visual: dict, informe: str, umbral: float = 0.5) -> dict:
    extraido = extraer_informe(informe)
    discrepancias, coincidencias = [], []
    for hallazgo in visual.get('findings', []):
        nombre = hallazgo['name']
        if nombre not in extraido:
            continue
        estado = extraido[nombre]['estado']
        if hallazgo['score'] >= umbral and estado == 'negado':
            discrepancias.append({'hallazgo':nombre,'mensaje':'El score experimental destacado y la negación del informe requieren revisión profesional. No se resuelve la discrepancia automáticamente.'})
        elif hallazgo['score'] >= umbral and estado == 'descrito':
            coincidencias.append({'hallazgo':nombre,'mensaje':'El término está descrito en el informe y tiene score experimental destacado; no confirma diagnóstico.'})
    return {'experimental':True,'informe_original':informe,'informe':extraido,
        'discrepancias':discrepancias,'coincidencias':coincidencias,'hallazgos_confirmados':[],
        'criterio_tecnico':{'umbral':umbral,'descripcion':'Criterio técnico no clínico para destacar scores normalizados XRV; no equivale a enfermedad ni a probabilidad.'},
        'advertencias':['Extracción limitada a términos explícitos de tres categorías; puede omitir o interpretar mal el contexto.',
                        'Un score bajo o ausencia de mención no descarta enfermedad. Revisión médica obligatoria.']}
