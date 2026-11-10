"""Mide el extractor de producción, no corrige sus errores."""
from app.imagenes.application.fusionar_hallazgos import extraer_informe, fusionar
from scripts.evaluacion_radiologia.casos import TERMINOS, validar_casos
from scripts.evaluacion_radiologia.metricas import clasificacion


def evaluar_textos(casos: list[dict]) -> dict:
    validar_casos(casos)
    filas, esperados, predichos = [], [], []
    confirmados = 0
    for c in casos:
        prediccion = {k: v['estado'] for k, v in extraer_informe(c['informe']).items()}
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
