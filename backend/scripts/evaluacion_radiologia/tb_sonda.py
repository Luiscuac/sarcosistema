"""A2: sonda lineal de TB sobre el DenseNet XRV congelado. NO es validación clínica.

Resultado (2026-11-15): sobre las 1024 características aprende el hospital (atajo, falla en Montgomery);
la combinación de los 18 scores sí generaliza y se exporta como indice_pulmonar_v1.json.

Entrena SOLO con Shenzhen y evalúa en Montgomery (otro país/equipo): simula llegar a un hospital nuevo.
El umbral de triaje se fija en Shenzhen (validación cruzada) para sensibilidad objetivo y se aplica
sin reajustar en Montgomery. Compara con la línea base (media de scores pulmonares XRV).
Uso (desde backend/): python -m scripts.evaluacion_radiologia.tb_sonda
"""
import argparse
import json
from pathlib import Path

from scripts.evaluacion_radiologia.tb_externa import (
    BASE_DIR, PULMONARES, _cargar_modelo, auc_ic, preparar,
)

DECAIMIENTOS = (1e-4, 1e-3, 1e-2, 1e-1, 1.0)
DECAIMIENTO_18 = 0.1


def entrenar_logistica(X, y, decaimiento, epocas=300):
    """Regresión logística L2 con estandarización calculada solo en entrenamiento."""
    import torch
    X = torch.as_tensor(X, dtype=torch.float32)
    y = torch.as_tensor(y, dtype=torch.float32)
    media, desv = X.mean(0), X.std(0) + 1e-6
    Xn = (X - media) / desv
    torch.manual_seed(0)
    lineal = torch.nn.Linear(X.shape[1], 1)
    opt = torch.optim.LBFGS(lineal.parameters(), lr=1, max_iter=epocas, line_search_fn='strong_wolfe')
    perdida_fn = torch.nn.BCEWithLogitsLoss()

    def paso():
        opt.zero_grad()
        perdida = perdida_fn(lineal(Xn).squeeze(1), y) + decaimiento * lineal.weight.pow(2).sum() / 2
        perdida.backward()
        return perdida
    opt.step(paso)
    w, b = lineal.weight.detach()[0], lineal.bias.detach()[0]
    return {'media': media, 'desv': desv, 'w': w, 'b': b}


def predecir(params, X):
    import torch
    X = torch.as_tensor(X, dtype=torch.float32)
    return torch.sigmoid(((X - params['media']) / params['desv']) @ params['w'] + params['b']).numpy()


def pliegues(n, k=5, semilla=0):
    import numpy as np
    orden = np.random.default_rng(semilla).permutation(n)
    return [orden[i::k] for i in range(k)]


def validacion_cruzada(X, y, decaimiento, k=5):
    """Predicciones fuera de pliegue (cada imagen se predice con un modelo que no la vio)."""
    import numpy as np
    pred = np.zeros(len(y))
    for prueba in pliegues(len(y), k):
        entreno = np.setdiff1d(np.arange(len(y)), prueba)
        pred[prueba] = predecir(entrenar_logistica(X[entreno], y[entreno], decaimiento), X[prueba])
    return pred


def umbral_para_sensibilidad(y, s, objetivo=0.9):
    import numpy as np
    positivos = np.sort(s[y == 1])
    return float(positivos[int(np.floor((1 - objetivo) * len(positivos)))])


def umbral_para_especificidad(y, s, objetivo=0.9):
    import numpy as np
    negativos = np.sort(s[y == 0])
    return float(negativos[min(len(negativos) - 1, int(np.ceil(objetivo * len(negativos))))])


def operar(y, s, umbral):
    import numpy as np
    tp = int(((s >= umbral) & (y == 1)).sum()); fn = int(((s < umbral) & (y == 1)).sum())
    tn = int(((s < umbral) & (y == 0)).sum()); fp = int(((s >= umbral) & (y == 0)).sum())
    return {'umbral': umbral, 'sensibilidad': tp / (tp + fn), 'especificidad': tn / (tn + fp),
            'tp': tp, 'fn': fn, 'tn': tn, 'fp': fp}


def extraer(datos: Path, filas: list[dict], modelos: Path, cache: Path):
    import numpy as np
    import torch
    if cache.exists():
        z = np.load(cache, allow_pickle=False)
        if list(z['ids']) == [f['id'] for f in filas]:
            return z['X']
    modelo, _ = _cargar_modelo(modelos)
    X = np.zeros((len(filas), 1024), dtype=np.float32)
    for i, f in enumerate(filas):
        tensor, _ = preparar(datos / f['conjunto'] / 'CXR_png' / (f['id'] + '.png'))
        with torch.inference_mode():
            X[i] = modelo.features2(tensor)[0].numpy()
        if (i + 1) % 50 == 0:
            print(f'características {i + 1}/{len(filas)}', flush=True)
    np.savez(cache, X=X, ids=np.array([f['id'] for f in filas]))
    return X


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datos', type=Path, default=BASE_DIR / '.datasets/tb-nlm')
    parser.add_argument('--resultados', type=Path, default=BASE_DIR / '.datasets/tb-nlm-resultados')
    parser.add_argument('--modelos', type=Path, default=BASE_DIR / '.models/radiologia')
    parser.add_argument('--sensibilidad', type=float, default=0.9)
    args = parser.parse_args()
    import numpy as np
    filas = json.loads((args.resultados / 'filas.json').read_text(encoding='utf-8'))
    X = extraer(args.datos, filas, args.modelos, args.resultados / 'caracteristicas.npz')
    y = np.array([f['tb'] for f in filas])
    base = np.array([sum(f['scores'][k] for k in PULMONARES) / len(PULMONARES) for f in filas])
    sz = np.array([f['conjunto'] == 'shenzhen' for f in filas])
    mc = ~sz

    cv = {d: auc_ic(y[sz], validacion_cruzada(X[sz], y[sz], d), repeticiones=200)[0] for d in DECAIMIENTOS}
    mejor = max(cv, key=cv.get)
    oof = validacion_cruzada(X[sz], y[sz], mejor)
    umbral = umbral_para_sensibilidad(y[sz], oof, args.sensibilidad)
    umbral_base = umbral_para_sensibilidad(y[sz], base[sz], args.sensibilidad)
    params = entrenar_logistica(X[sz], y[sz], mejor)
    externo = predecir(params, X[mc])

    def bloque(yy, s, u):
        a, lo, hi = auc_ic(yy, s)
        return {'auroc': a, 'ic95': [lo, hi], f'operacion_sens{int(args.sensibilidad * 100)}': operar(yy, s, u)}
    resumen = {
        'validacion_clinica': False,
        'diseno': 'Entrena en Shenzhen (5-fold CV elige L2 y umbral); prueba externa en Montgomery sin reajustar.',
        'decaimiento_cv': cv, 'decaimiento_elegido': mejor,
        'shenzhen_cv': {'sonda': bloque(y[sz], oof, umbral), 'linea_base': bloque(y[sz], base[sz], umbral_base)},
        'montgomery_externo': {'sonda': bloque(y[mc], externo, umbral), 'linea_base': bloque(y[mc], base[mc], umbral_base)},
        'subgrupos_montgomery_sonda': {
            sexo: auc_ic(y[mc][m], externo[m], repeticiones=500)
            for sexo in ('male', 'female')
            if (m := np.array([f['sexo'] == sexo for f, es in zip(filas, mc) if es])).any() and 0 < y[mc][m].sum() < m.sum()},
    }
    # Atajo: si las características distinguen el hospital, la sonda puede aprender el equipo y no la TB.
    sitio = sz.astype(int)
    resumen['atajo_auc_distinguir_hospital_1024'] = auc_ic(sitio, validacion_cruzada(X, sitio, mejor), repeticiones=100)[0]

    # Variante elegida para producción: combinación de los 18 scores (pocos parámetros, generaliza).
    from app.imagenes.domain.vision import TARGETS
    S = np.array([[f['scores'][k] for k in TARGETS] for f in filas], dtype=np.float32)
    oof18 = validacion_cruzada(S[sz], y[sz], DECAIMIENTO_18)
    p18 = entrenar_logistica(S[sz], y[sz], DECAIMIENTO_18)
    ext18 = predecir(p18, S[mc])
    u_media = umbral_para_sensibilidad(y[sz], oof18, args.sensibilidad)
    u_alta = umbral_para_especificidad(y[sz], oof18, 0.9)
    resumen['indice_18'] = {
        'shenzhen_cv': bloque(y[sz], oof18, u_media), 'montgomery_externo': bloque(y[mc], ext18, u_media),
        'atajo_auc_distinguir_hospital_18': auc_ic(sitio, validacion_cruzada(S, sitio, DECAIMIENTO_18), repeticiones=100)[0]}
    artefacto = {
        'version': 'indice-pulmonar-v1', 'modelo_base': 'densenet121-res224-all (XRV 1.5.7)',
        'etiquetas': list(TARGETS), 'coeficientes': p18['w'].tolist(), 'intercepto': float(p18['b']),
        'media': p18['media'].tolist(), 'desviacion': p18['desv'].tolist(), 'decaimiento_l2': DECAIMIENTO_18,
        'entrenamiento': 'Shenzhen (NLM/NIH y Shenzhen No.3 People\'s Hospital), 662 radiografías, TB vs normal. '
                         'Citar Jaeger 2014 y Candemir 2014. Solo coeficientes derivados; no contiene imágenes.',
        'metricas': {'auroc_shenzhen_cv': resumen['indice_18']['shenzhen_cv']['auroc'],
                     'auroc_montgomery_externo': resumen['indice_18']['montgomery_externo']['auroc']},
        'umbrales_provisionales': {'media': u_media, 'alta': u_alta,
                                   'nota': 'Fijados en Shenzhen (sensibilidad 90 % / especificidad 90 %). '
                                           'No se transfieren entre hospitales: calibrar localmente.'},
        'uso': 'Ordenar la revisión. No es diagnóstico ni probabilidad de tuberculosis.'}
    destino = BASE_DIR / 'app/imagenes/infrastructure/vision/indice_pulmonar_v1.json'
    destino.write_text(json.dumps(artefacto, indent=1, ensure_ascii=False), encoding='utf-8')
    (args.resultados / 'sonda_tb.json').write_text(json.dumps(resumen, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in resumen.items() if k != 'decaimiento_cv'}, indent=1))


if __name__ == '__main__':
    main()
