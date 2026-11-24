"""Concordancia médico–IA y calibración local de umbrales (sin torch ni numpy).

La referencia del índice es la lectura del médico al revisar (`anormal_confirmado`), no un diagnóstico
confirmado; la del patrón TB es la confirmación bacteriológica que registra el médico (`tb_confirmada`). Con pocos casos no se calcula nada: los umbrales sugeridos nunca se aplican solos.
"""
import math

MIN_CASOS_POR_CLASE = 20


def auroc(etiquetas: list[int], valores: list[float]) -> float | None:
    positivos = [v for e, v in zip(etiquetas, valores) if e == 1]
    negativos = [v for e, v in zip(etiquetas, valores) if e == 0]
    if not positivos or not negativos:
        return None
    pares = sum((p > n) + 0.5 * (p == n) for p in positivos for n in negativos)
    return pares / (len(positivos) * len(negativos))


def umbral_para_sensibilidad(etiquetas, valores, objetivo=0.9) -> float:
    positivos = sorted(v for e, v in zip(etiquetas, valores) if e == 1)
    return positivos[int(math.floor((1 - objetivo) * len(positivos)))]


def umbral_para_especificidad(etiquetas, valores, objetivo=0.9) -> float:
    negativos = sorted(v for e, v in zip(etiquetas, valores) if e == 0)
    return negativos[min(len(negativos) - 1, int(math.ceil(objetivo * len(negativos))))]


def operar(etiquetas, valores, umbral) -> dict:
    tp = sum(e == 1 and v >= umbral for e, v in zip(etiquetas, valores))
    fn = sum(e == 1 and v < umbral for e, v in zip(etiquetas, valores))
    tn = sum(e == 0 and v < umbral for e, v in zip(etiquetas, valores))
    fp = sum(e == 0 and v >= umbral for e, v in zip(etiquetas, valores))
    return {'umbral': umbral, 'sensibilidad': tp / (tp + fn) if tp + fn else None,
            'especificidad': tn / (tn + fp) if tn + fp else None}


def calibrar(casos: list[tuple[float, bool]], minimo: int = MIN_CASOS_POR_CLASE) -> dict:
    """casos: (índice pulmonar, lectura del médico anormal). Devuelve AUC local y umbrales sugeridos."""
    validos = [(float(i), int(a)) for i, a in casos if i is not None and a is not None and math.isfinite(float(i))]
    anormales = sum(a for _, a in validos)
    normales = len(validos) - anormales
    base = {'casos': len(validos), 'anormales': anormales, 'normales': normales, 'minimo_por_clase': minimo,
            'faltan_anormales': max(0, minimo - anormales), 'faltan_normales': max(0, minimo - normales)}
    if anormales < minimo or normales < minimo:
        return base | {'estado': 'insuficiente',
                       'mensaje': f'Faltan casos revisados para calibrar: se necesitan al menos {minimo} anormales y {minimo} normales.'}
    etiquetas = [a for _, a in validos]
    valores = [i for i, _ in validos]
    media = umbral_para_sensibilidad(etiquetas, valores, 0.9)
    alta = max(media, umbral_para_especificidad(etiquetas, valores, 0.9))
    return base | {'estado': 'calibrado', 'auroc_local': auroc(etiquetas, valores),
                   'umbral_sugerido_media': media, 'umbral_sugerido_alta': alta,
                   'operacion_media': operar(etiquetas, valores, media), 'operacion_alta': operar(etiquetas, valores, alta),
                   'mensaje': 'Umbrales sugeridos con lecturas médicas locales. Revísalos y, si corresponde, configúralos en '
                              'RADIOLOGY_TRIAGE_UMBRAL_ALTA/MEDIA; no se aplican automáticamente.'}


def calibrar_tb(casos: list[tuple[float, bool, str]], version: str, umbral_actual: float,
                minimo: int = MIN_CASOS_POR_CLASE) -> dict:
    """casos: (valor del patrón TB, TB confirmada por el médico, versión del patrón).

    Solo se calibran casos de la versión en uso: v1 (modelo base) y v2 (ensamble) no son comparables.
    El corte sugerido mantiene la regla del artefacto (especificidad 90 % frente a lo no TB).
    """
    validos = [(float(v), int(c)) for v, c, ver in casos
               if v is not None and c is not None and ver == version and math.isfinite(float(v))]
    con_tb = sum(c for _, c in validos)
    sin_tb = len(validos) - con_tb
    base = {'version': version, 'umbral_actual': umbral_actual, 'casos': len(validos), 'con_tb': con_tb,
            'sin_tb': sin_tb, 'minimo_por_clase': minimo,
            'faltan_con_tb': max(0, minimo - con_tb), 'faltan_sin_tb': max(0, minimo - sin_tb),
            'otras_versiones': sum(1 for v, c, ver in casos if c is not None and v is not None and ver != version)}
    if con_tb < minimo or sin_tb < minimo:
        return base | {'estado': 'insuficiente',
                       'mensaje': f'Faltan casos con TB confirmada o descartada: se necesitan al menos {minimo} de cada tipo.'}
    etiquetas = [c for _, c in validos]
    valores = [v for v, _ in validos]
    sugerido = umbral_para_especificidad(etiquetas, valores, 0.9)
    return base | {'estado': 'calibrado', 'auroc_local': auroc(etiquetas, valores),
                   'operacion_actual': operar(etiquetas, valores, umbral_actual),
                   'umbral_sugerido': sugerido, 'operacion_sugerida': operar(etiquetas, valores, sugerido),
                   'mensaje': 'Corte sugerido con casos locales (especificidad 90 %). Revísalo y, si corresponde, '
                              'configúralo en RADIOLOGY_TB_UMBRAL_COMPATIBLE; se aplica a los análisis nuevos, no solo.'}


def resumir_concordancia(filas: list[dict], patron_tb: dict | None = None) -> dict:
    """filas: un análisis cada una (estado, decision de su última revisión, anormal_confirmado, indice,
    discrepancias, omisiones, coincidencias). Solo agregados: sin pacientes ni identificadores."""
    completados = [f for f in filas if f['estado'] == 'completado']
    revisados = [f for f in completados if f.get('decision')]
    decisiones = {d: sum(f['decision'] == d for f in revisados) for d in ('aceptada_como_propuesta', 'corregida', 'rechazada')}
    avisos = {k: sum(f.get(k) or 0 for f in completados) for k in ('discrepancias', 'omisiones', 'coincidencias')}
    con_avisos = [f for f in revisados if (f.get('discrepancias') or 0) + (f.get('omisiones') or 0) > 0]
    lecturas = [f for f in revisados if f.get('anormal_confirmado') is not None]
    return {
        'analisis_totales': len(filas), 'analisis_completados': len(completados),
        'analisis_revisados': len(revisados),
        'tasa_revision': len(revisados) / len(completados) if completados else None,
        'decisiones': decisiones,
        'tasa_aceptacion': decisiones['aceptada_como_propuesta'] / len(revisados) if revisados else None,
        'avisos_generados': avisos,
        'revisados_con_avisos': len(con_avisos),
        'revisados_con_avisos_corregidos_o_rechazados': sum(f['decision'] != 'aceptada_como_propuesta' for f in con_avisos),
        'lecturas_medicas': {'anormal': sum(bool(f['anormal_confirmado']) for f in lecturas),
                             'normal': sum(not f['anormal_confirmado'] for f in lecturas)},
        'calibracion': calibrar([(f.get('indice'), f['anormal_confirmado']) for f in lecturas]),
        'lecturas_tb': {'confirmada': sum(f.get('tb_confirmada') is True for f in revisados),
                        'descartada': sum(f.get('tb_confirmada') is False for f in revisados)},
        'calibracion_tb': calibrar_tb([(f.get('patron_tb'), f.get('tb_confirmada'), f.get('patron_tb_version'))
                                       for f in revisados], **patron_tb) if patron_tb else None,
        'nota': 'La referencia es la lectura del médico al revisar la propuesta, no un diagnóstico confirmado.',
    }
