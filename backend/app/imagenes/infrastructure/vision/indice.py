"""Índice pulmonar experimental: combinación logística de los 18 scores XRV.

Sirve para ORDENAR estudios por prioridad de revisión. No es diagnóstico ni probabilidad de
tuberculosis; su umbral no se transfiere entre hospitales (ver docs/imagenes, evaluación externa TB).
"""
from functools import lru_cache
import json
import math
from pathlib import Path

ARTEFACTO = Path(__file__).with_name('indice_pulmonar_v1.json')


@lru_cache(maxsize=1)
def cargar_indice(ruta: str = str(ARTEFACTO)) -> dict:
    datos = json.loads(Path(ruta).read_text(encoding='utf-8'))
    n = len(datos['etiquetas'])
    if not (len(datos['coeficientes']) == len(datos['media']) == len(datos['desviacion']) == n):
        raise ValueError('Artefacto del índice pulmonar incompleto.')
    return datos


def calcular_indice(scores: dict, artefacto: dict | None = None, top: int = 5) -> dict:
    a = artefacto or cargar_indice()
    aportes = []
    logit = a['intercepto']
    for nombre, w, m, d in zip(a['etiquetas'], a['coeficientes'], a['media'], a['desviacion']):
        aporte = w * (scores[nombre] - m) / d
        logit += aporte
        aportes.append({'name': nombre, 'aporte': aporte})
    aportes.sort(key=lambda x: x['aporte'], reverse=True)
    return {'valor': 1 / (1 + math.exp(-logit)), 'version': a['version'],
            'contribuciones': [x for x in aportes[:top] if x['aporte'] > 0],
            'advertencia': 'Índice experimental para ordenar la revisión; no es diagnóstico ni probabilidad de tuberculosis. '
                           'Su umbral no se transfiere entre hospitales.'}
