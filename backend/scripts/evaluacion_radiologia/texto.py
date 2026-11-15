"""Mide el extractor de producción, no corrige sus errores."""
from app.imagenes.application.fusionar_hallazgos import extraer_informe, fusionar
from scripts.evaluacion_radiologia.casos import TERMINOS, validar_casos
from scripts.evaluacion_radiologia.metricas import clasificacion


def evaluar_textos(casos: list[dict]) -> dict:
    validar_casos(casos)
    filas, esperados, predichos = [], [], []
    confirmados = 0
    for c in casos:
        prediccion = {k: v['estado'] for k, v in extraer_informe(c['informe'], TERMINOS).items()}
        # Control contractual sintético: NO procede de una imagen.
        visual = {'findings': [{'name': k, 'score': .8} for k in TERMINOS]}
        combinado = fusionar(visual, c['informe'])
        confirmados += len(combinado['hallazgos_confirmados'])
        discrepancias_ref = {k for k, v in c['referencia'].items() if v == 'negado'}
        discrepancias = {d['hallazgo'] for d in combinado['discrepancias']}
        filas.append({'id': c['id'], 'grupo': c['grupo'], 'familia': c['familia'],
            'informe': c['informe'], 'objetivo': c['objetivo'], 'referencia': c['referencia'],
            'prediccion': prediccion, 'acierto_objetivo': prediccion[c['objetivo']] == c['referencia'][c['objetivo']],
            'scores_synthetic': True, 'discrepancias_referencia': sorted(discrepancias_ref),
            'discrepancias_observadas': sorted(discrepancias)})
        esperados.extend(c['referencia'].values())
        predichos.extend(prediccion.values())
    def metrica(sub):
        return clasificacion([f['referencia'][f['objetivo']] for f in sub],
                             [f['prediccion'][f['objetivo']] for f in sub])
    return {'synthetic': True, 'validacion_clinica': False, 'n_casos': len(filas),
        'advertencia': '100 familias compartidas por tres términos; casos no independientes; referencia de autoría no experta.',
        'objetivo': metrica(filas), 'todas_etiquetas': clasificacion(esperados, predichos),
        'por_grupo': {g: metrica([f for f in filas if f['grupo'] == g]) for g in sorted({f['grupo'] for f in filas})},
        'por_hallazgo': {k: metrica([f for f in filas if f['objetivo'] == k]) for k in TERMINOS},
        'control_scores_sinteticos': {'n': len(filas), 'diagnosticos_confirmados': confirmados,
            'discrepancia_exacta': sum(f['discrepancias_referencia'] == f['discrepancias_observadas'] for f in filas)},
        'casos': filas}


def evaluar_textos_18(casos: list[dict]) -> dict:
    """Extracción en las 18 categorías: acierto en la categoría objetivo y falsos positivos en las demás."""
    from scripts.evaluacion_radiologia.casos import TERMINOS_18
    filas = []
    for c in casos:
        prediccion = {k: v['estado'] for k, v in extraer_informe(c['informe'], TERMINOS_18).items()}
        filas.append({'grupo': c['grupo'], 'objetivo': c['objetivo'], 'informe': c['informe'],
                      'esperado': c['referencia'][c['objetivo']], 'predicho': prediccion[c['objetivo']],
                      'falsas_menciones': sorted(k for k, v in prediccion.items() if k != c['objetivo'] and v != 'no_mencionado')})

    def metrica(sub):
        return clasificacion([f['esperado'] for f in sub], [f['predicho'] for f in sub])
    return {'synthetic': True, 'validacion_clinica': False, 'n_casos': len(filas),
            'objetivo': metrica(filas),
            'por_grupo': {g: metrica([f for f in filas if f['grupo'] == g]) for g in sorted({f['grupo'] for f in filas})},
            'por_hallazgo': {k: metrica([f for f in filas if f['objetivo'] == k]) for k in TERMINOS_18},
            'casos_con_falsas_menciones': sum(bool(f['falsas_menciones']) for f in filas),
            'errores': [f for f in filas if f['esperado'] != f['predicho'] or f['falsas_menciones']]}
