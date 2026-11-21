"""TB: "deja un sitio fuera" (LOSO) sobre el DenseNet XRV congelado. NO es validación clínica.

Para cada sitio (tbx11k, shenzhen, montgomery, dadb) se entrena con los OTROS y se prueba en él: estima cómo
rendiría el método al llegar a un hospital nuevo. Compara, con el mismo protocolo:
- indice_v1: el índice pulmonar de producción tal cual (referencia; v1 se ajustó con Shenzhen).
- s18: logística sobre las 18 salidas XRV (re-ajustada en cada pliegue).
- f1024: logística sobre las 1024 características (propensa a aprender el hospital).
- s18+f1024 PCA: 18 salidas + 32 componentes principales de las características.
El umbral se fija con los sitios de entrenamiento (sensibilidad 90 %) y se aplica sin reajustar.
Uso (desde backend/, con .venv-gpu): python -m scripts.evaluacion_radiologia.tb_loso
"""
import json
from pathlib import Path

from scripts.evaluacion_radiologia.tb_entrenar import (
    BASE_DIR, auc_ic, caracteristicas, cargar_modelo, operar, umbral_sensibilidad,
)

SITIOS = ('tbx11k', 'shenzhen', 'montgomery', 'dadb')


def extraer(cache: Path, salida: Path):
    import numpy as np
    import torch
    if salida.exists():
        return dict(np.load(salida))
    d = np.load(cache)
    modelo, targets = cargar_modelo(BASE_DIR / '.models/radiologia')
    modelo = modelo.cuda().eval()
    F, S = [], []
    with torch.inference_mode():
        for i in range(0, len(d['tb']), 128):
            x = torch.from_numpy(d['X'][i:i + 128].astype(np.float32)).unsqueeze(1).cuda()
            f = caracteristicas(modelo, x)
            F.append(f.cpu().numpy())
            S.append(modelo(x).cpu().numpy())
    datos = {'F': np.concatenate(F), 'S': np.concatenate(S), 'tb': d['tb'], 'sitio': d['sitio'],
             'clase': d['clase'], 'targets': np.array(targets)}
    np.savez(salida, **datos)
    return datos


def main():
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    base = BASE_DIR / '.datasets/tb-entrenamiento'
    d = extraer(base / 'cache.npz', base / 'caracteristicas.npz')
    y, sitio = d['tb'].astype(int), d['sitio']
    art = json.loads((BASE_DIR / 'app/imagenes/infrastructure/vision/indice_pulmonar_v1.json').read_text(encoding='utf-8'))
    orden = [list(d['targets']).index(e) for e in art['etiquetas']]
    S18 = d['S'][:, orden]
    indice = ((S18 - art['media']) / np.array(art['desviacion']) * art['coeficientes']).sum(1) + art['intercepto']

    def logistica(C):
        return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=3000, class_weight='balanced'))

    def pca_f():
        return make_pipeline(StandardScaler(), PCA(32, random_state=0))

    metodos = {'s18': lambda: (logistica(0.1), lambda m: S18),
               'f1024': lambda: (logistica(0.01), lambda m: d['F'])}
    resultados = {'validacion_clinica': False, 'protocolo': 'deja-un-sitio-fuera', 'sitios': {}}
    for fuera in SITIOS:
        te, tr = np.where(sitio == fuera)[0], np.where(sitio != fuera)[0]
        r = {'n': int(len(te)), 'tb': int(y[te].sum()), 'entrena_con': [s for s in SITIOS if s != fuera]}
        u = umbral_sensibilidad(y[tr], indice[tr])
        r['indice_v1'] = {'auc_ic95': auc_ic(y[te], indice[te]), **operar(y[te], indice[te], u)}
        for nombre, fabrica in metodos.items():
            modelo, X = fabrica()
            X = X(None)
            modelo.fit(X[tr], y[tr])
            p = modelo.decision_function(X)
            u = umbral_sensibilidad(y[tr], p[tr])
            r[nombre] = {'auc_ic95': auc_ic(y[te], p[te]), **operar(y[te], p[te], u)}
        pca = pca_f().fit(d['F'][tr])
        X = np.hstack([S18, pca.transform(d['F'])])
        modelo = logistica(0.05).fit(X[tr], y[tr])
        p = modelo.decision_function(X)
        u = umbral_sensibilidad(y[tr], p[tr])
        r['s18+pca32'] = {'auc_ic95': auc_ic(y[te], p[te]), **operar(y[te], p[te], u)}
        if fuera == 'tbx11k':
            sick = te[np.isin(d['clase'][te], ['tb', 'enfermo_no_tb'])]
            r['tb_vs_enfermo_no_tb'] = {'indice_v1': auc_ic(y[sick], indice[sick])}
        resultados['sitios'][fuera] = r
        print(fuera, {k: round(v['auc_ic95'][0], 3) for k, v in r.items() if isinstance(v, dict) and 'auc_ic95' in v}, flush=True)
    (base / 'resultados_loso.json').write_text(json.dumps(resultados, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
