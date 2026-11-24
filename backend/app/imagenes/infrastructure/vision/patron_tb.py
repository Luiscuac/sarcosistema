"""Patrón de tuberculosis experimental: ¿la imagen tiene un patrón compatible con TB?

Logística sobre los 18 scores XRV (artefacto patron_tb_v1.json, TBX11K: TB vs sanos + otras enfermedades).
Solo AVISA cuando ve el patrón (nivel 'compatible'); nunca descarta TB: en hospitales externos el corte deja
pasar muchas TB y marca algunos sanos (ver 'limites' del artefacto).
No es diagnóstico: la confirmación es bacteriológica (baciloscopía, GeneXpert, cultivo).
"""
from functools import lru_cache
import json
import math
from pathlib import Path

ARTEFACTO = Path(__file__).with_name('patron_tb_v1.json')
# v2: entradas = promedio del modelo base y 6 especialistas XRV (ensamble.py). Mejor en hospitales externos.
ARTEFACTO_ENSAMBLE = Path(__file__).with_name('patron_tb_v2.json')
ADVERTENCIA = ('Señal experimental: indica parecido con patrones de tuberculosis, no diagnóstico. '
               'No descarta TB cuando no aparece. Confirmar con baciloscopía o GeneXpert.')


@lru_cache(maxsize=1)
def cargar_patron(ruta: str = str(ARTEFACTO)) -> dict:
    datos = json.loads(Path(ruta).read_text(encoding='utf-8'))
    n = len(datos['etiquetas'])
    if not (len(datos['coeficientes']) == len(datos['media']) == len(datos['desviacion']) == n):
        raise ValueError('Artefacto del patrón de TB incompleto.')
    if not 0 < datos['umbrales']['compatible'] < 1:
        raise ValueError('Umbral del patrón de TB fuera de rango.')
    return datos


def patron_en_uso(ensamble_habilitado: bool, umbral_local: float | None) -> dict:
    """Versión del patrón que usan los análisis nuevos y su corte (local si está configurado)."""
    from app.imagenes.infrastructure.vision.ensamble import ensamble_preparado
    ruta = ARTEFACTO_ENSAMBLE if ensamble_habilitado and ensamble_preparado() else ARTEFACTO
    a = cargar_patron(str(ruta))
    return {'version': a['version'],
            'umbral_actual': a['umbrales']['compatible'] if umbral_local is None else umbral_local}


def calcular_patron_tb(scores: dict, artefacto: dict | None = None, umbral: float | None = None) -> dict:
    """scores: 18 salidas del modelo base (v1) o su promedio con el ensamble (v2, `artefacto` del ensamble).

    `umbral`: corte calibrado localmente (RADIOLOGY_TB_UMBRAL_COMPATIBLE); si es None se usa el del artefacto.
    """
    a = artefacto or cargar_patron()
    corte = a['umbrales']['compatible'] if umbral is None else umbral
    logit = a['intercepto'] + sum(w * (scores[n] - m) / d for n, w, m, d in
                                  zip(a['etiquetas'], a['coeficientes'], a['media'], a['desviacion']))
    valor = 1 / (1 + math.exp(-logit))
    nivel = 'compatible' if valor >= corte else None
    return {'valor': valor, 'nivel': nivel, 'version': a['version'], 'ensamble': bool(a.get('requiere_ensamble')),
            'umbral': corte, 'umbral_origen': 'artefacto' if umbral is None else 'local', 'advertencia': ADVERTENCIA}
