"""Respuesta extractiva: evidencia documental, no interpretación del paciente."""
import math
import re

TEMAS = {
    'derrame': ('derrame', 'pleural effusion'),
    'consolidacion': ('consolidación', 'consolidacion', 'consolidation'),
    'cardiomegalia': ('cardiomegalia', 'cardiomegaly', 'cardiac enlargement'),
    'limitaciones': ('limitacion', 'limitación', 'limitations', 'sensitivity'),
    'normal': ('normal',),
}


def responder_con_evidencia(pregunta: str, recuperados: list[dict]) -> dict:
    respuesta = {'estado': 'informacion_insuficiente',
        'mensaje': 'No existe evidencia suficiente en la base local para responder esta consulta.',
        'experimental': True, 'modo': 'extractivo_sin_llm', 'informe_original': pregunta,
        'hallazgos_confirmados': [], 'evidencia': [],
        'advertencias': ['La recuperación no confirma ni descarta hallazgos del paciente.',
                         'Las citas conservan el idioma original; no son una recomendación clínica.']}
    if not pregunta.strip() or len(pregunta) > 4000:
        return respuesta
    q = pregunta.lower()
    if re.search(r'ignora|ignore|system prompt|instrucciones|diagnostica|tratamiento|dosifica', q):
        return respuesta
    temas = [sinonimos for sinonimos in TEMAS.values() if any(t in q for t in sinonimos)]
    if not temas:
        return respuesta
    for e in recuperados:
        distancia = e['distancia']
        if not math.isfinite(distancia) or distancia > 0.45:
            continue
        if not (0 <= e['inicio'] < e['fin'] <= len(e['contenido'])):
            continue
        if e['contenido'][e['inicio']:e['fin']] != e['texto']:
            continue
        if not any(any(t in e['texto'].lower() for t in sinonimos) for sinonimos in temas):
            continue
        if TEMAS['limitaciones'] in temas:
            # Sensibilidad de otra modalidad/procedimiento no prueba límites de RX.
            oraciones = re.split(r'(?<=[.!?])\s+', e['texto'].lower())
            if not any(re.search(r'chest (?:radiograph|x.ray)|radiograf[ií]a', oracion)
                       and re.search(r'limit|sensitiv|miss|cannot|insensitiv|sensi', oracion)
                       and not re.search(r'\bct\b|computed tomography|biopsy|tomograf|biopsia', oracion)
                       for oracion in oraciones):
                continue
        respuesta['evidencia'].append({k: e[k] for k in (
            'id', 'documento_id', 'titulo', 'fuente', 'licencia', 'sha256', 'seccion', 'inicio', 'fin')}
            | {'cita': e['texto'], 'distancia_coseno': distancia})
    if respuesta['evidencia']:
        respuesta['estado'] = 'evidencia_recuperada'
        respuesta['mensaje'] = 'Fragmentos documentales relacionados; requieren interpretación profesional.'
    return respuesta
