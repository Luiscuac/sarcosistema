"""Corpus de desafío de autoría sintética NO revisado por especialistas.

Etiquetas declaradas antes de ejecutar el extractor. Familia compartida entre
hallazgos: 300 textos no representan 300 observaciones clínicas independientes.
"""
from collections import Counter

TERMINOS = {'Consolidation': 'consolidación', 'Effusion': 'derrame pleural',
            'Cardiomegaly': 'cardiomegalia'}
POSITIVOS = [
    'Se observa {t}.', 'Hay {t}.', 'Se describe {t}.', 'Hallazgo presente: {t}.',
    'El informe muestra {t}.', 'Se identifica {t}.', 'Se aprecia {t}.',
    'Se evidencia {t}.', 'Hallazgo radiográfico: {t}.', 'Persiste {t}.',
    'Aumento de {t}.', 'Disminución de {t}.', 'Progresión de {t}.',
    'Resolución parcial de {t}.', 'Aparición de {t}.', 'Se confirma presencia de {t}.',
    'Respecto al estudio previo, persiste {t}.', 'El hallazgo principal es {t}.',
    'En la imagen frontal se observa {t}.', 'El control documenta {t}.',
    'Se vuelve a identificar {t}.', 'Existe evidencia radiográfica de {t}.',
    'La lectura actual describe {t}.', 'En el examen actual hay {t}.',
    'La impresión radiológica incluye {t}.',
]
NEGATIVOS = [
    'No hay {t}.', 'Sin {t}.', 'Ausencia de {t}.', 'No se observa {t}.',
    'No se identifica {t}.', 'No se aprecia {t}.', 'No se evidencia {t}.',
    'Sin signos de {t}.', 'Sin evidencia de {t}.', 'No presenta {t}.',
    'No existe {t}.', 'No se detecta {t}.', 'Se descarta {t}.',
    '{T} no evidente.', '{T} ausente.', 'No persiste {t}.',
    'Sin hallazgos de {t}.', 'No se demuestra {t}.',
    'No hay datos de {t}.', 'No aparecen signos de {t}.',
    'Sin indicios radiográficos de {t}.', 'No se visualiza {t}.',
    'Sin manifestaciones de {t}.', 'No se reconoce {t}.',
    'Negativo para {t}.',
]
# Las etiquetas de incertidumbre no se deducen del comportamiento del extractor.
AMBIGUOS = [
    ('Posible {t}.', 'incierto'), ('Probable {t}.', 'incierto'),
    ('Sospecha de {t}.', 'incierto'), ('Dudosa {t}.', 'incierto'),
    ('No se puede descartar {t}.', 'incierto'), ('No puede descartarse {t}.', 'incierto'),
    ('{T}?', 'incierto'), ('¿{T}?', 'incierto'),
    ('A descartar {t}.', 'incierto'), ('Sugestivo de {t}.', 'incierto'),
    ('Evaluar posible {t}.', 'incierto'), ('{T} sin cambios.', 'ambiguo'),
    ('Sin cambios respecto a {t}.', 'ambiguo'),
    ('Sin variación de {t}.', 'ambiguo'), ('No hay cambios en {t}.', 'ambiguo'),
    ('No se observan cambios en {t}.', 'ambiguo'),
    ('Antecedente de {t}; presencia actual no determinada.', 'ambiguo'),
    ('No se puede evaluar {t} por limitación técnica.', 'incierto'),
    ('La presencia de {t} es indeterminada.', 'incierto'),
    ('Se solicita valorar {t}, sin afirmar su presencia.', 'incierto'),
    ('{T} no descartable.', 'incierto'),
    ('La evaluación de {t} no es concluyente.', 'incierto'),
    ('Podría corresponder a {t}.', 'incierto'),
    ('No es posible confirmar ni excluir {t}.', 'incierto'),
    ('{T}: evaluación pendiente.', 'incierto'),
]
CONTRADICTORIOS = [
    'Hay {t}. No hay {t}.', 'Se observa {t}. Sin {t}.',
    'Ausencia de {t}. Se describe {t}.', 'Existe {t}; no existe {t}.',
    'Se identifica {t}, pero no se observa {t}.',
    'Se aprecia {t}; sin evidencia de {t}.',
    'Sin signos de {t}; se evidencia {t}.',
    'No presenta {t}. El examen muestra {t}.',
    'El hallazgo es {t}; ausencia de {t}.',
    'No se detecta {t}; se detecta {t}.',
    'Persiste {t}; no persiste {t}.',
    'No se demuestra {t}; se demuestra {t}.',
    'Se visualiza {t}. No se visualiza {t}.',
    'Negativo para {t}; positivo para {t}.',
    '{T} ausente; {t} presente.',
    'No hay datos de {t}; hay datos de {t}.',
    'Se confirma {t}; se descarta {t}.',
    'Sin indicios de {t}; indicios de {t} presentes.',
    'Impresión: {t}. Conclusión: sin {t}.',
    'Lectura inicial: no hay {t}. Lectura final: hay {t}.',
    'Cuerpo del informe: {t}. Resumen: ausencia de {t}.',
    'Hay {t} y no hay {t}.', 'Sin {t} y se observa {t}.',
    'Se aprecia {t}, no se aprecia {t}.',
    'No se reconoce {t}; se reconoce {t}.',
]


def generar_casos() -> list[dict]:
    casos = []
    for grupo, plantillas in [('positivo', POSITIVOS), ('negativo', NEGATIVOS),
                              ('ambiguo', AMBIGUOS), ('contradictorio', CONTRADICTORIOS)]:
        for objetivo, termino in TERMINOS.items():
            for numero, plantilla in enumerate(plantillas, 1):
                estado = {'positivo': 'descrito', 'negativo': 'negado',
                          'contradictorio': 'ambiguo'}.get(grupo)
                if grupo == 'ambiguo':
                    plantilla, estado = plantilla
                texto = plantilla.format(t=termino, T=termino.capitalize())
                referencia = {k: 'no_mencionado' for k in TERMINOS}
                referencia[objetivo] = estado
                if grupo == 'positivo' and objetivo == 'Cardiomegaly' and numero == 25:
                    texto = 'No hay derrame pleural y hay cardiomegalia.'
                    referencia['Effusion'] = 'negado'
                casos.append({'id': f'SYN-{grupo}-{objetivo}-{numero:02d}',
                    'synthetic': True, 'etiqueta': 'CASO SINTÉTICO — NO VALIDACIÓN CLÍNICA',
                    'grupo': grupo, 'familia': f'{grupo}-{numero:02d}', 'objetivo': objetivo,
                    'contexto': 'Persona adulta ficticia; radiografía frontal ficticia; sin imagen emparejada.',
                    'informe': texto, 'referencia': referencia,
                    'referencia_origen': 'Autoría sintética, no adjudicación médica'})
    return casos


def validar_casos(casos: list[dict]) -> None:
    if len(casos) != 300 or len({c['id'] for c in casos}) != 300 or len({c['informe'] for c in casos}) != 300:
        raise ValueError('Se requieren 300 casos distintos')
    if set(Counter((c['grupo'], c['objetivo']) for c in casos).values()) != {25}:
        raise ValueError('Distribución incompatible')
    estados = {'descrito', 'negado', 'ambiguo', 'incierto', 'no_mencionado'}
    for c in casos:
        if c['synthetic'] is not True or set(c['referencia']) != set(TERMINOS) or not set(c['referencia'].values()) <= estados:
            raise ValueError('Etiquetado incompatible')
