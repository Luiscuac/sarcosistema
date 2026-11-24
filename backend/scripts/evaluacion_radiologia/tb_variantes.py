"""Compara variantes de entrada/modelo con el MISMO protocolo de TB. NO es validación clínica.

Variantes:
- base224: DenseNet XRV 'all' sobre cache.npz (producción actual).
- recorte / mascara: DenseNet 'all' sobre las cachés "solo pulmones" (tb_cache_pulmones).
- resnet512: ResNet50 XRV 'resnet50-res512-all' sobre cache512 (mayor resolución).
Por variante (salidas guardadas en salidas_<variante>.npz para no recalcular):
- índice: logística de 18 salidas ajustada SOLO en Shenzhen -> AUC Montgomery, India, TBX11K val.
- patrón TB: logística de 18 salidas ajustada SOLO en TBX11K train -> AUC Shenzhen, Montgomery, India; aviso al
  corte de especificidad 90 % en TBX11K val (TB detectadas / sin TB con aviso).
- cabeza de características (1024/2048) ajustada en TBX11K train -> AUC externos (la que antes aprendía el hospital).
- deja-un-sitio-fuera (LOSO) para 18 salidas y para características: AUC en cada sitio dejado fuera.
Combinaciones: se pueden promediar salidas de varias variantes (--combinar base224+resnet512).
Uso (desde backend/, con .venv-gpu): python -m scripts.evaluacion_radiologia.tb_variantes --variantes base224,recorte
"""
import argparse
import json
import math

from scripts.evaluacion_radiologia.tb_entrenar import BASE_DIR, auc, caracteristicas

DATOS = BASE_DIR / '.datasets/tb-entrenamiento'
SITIOS = ('tbx11k', 'shenzhen', 'montgomery', 'dadb')


def _modelo(variante):
    import torchxrayvision as xrv
    if variante == 'resnet512':
        return xrv.models.ResNet(weights='resnet50-res512-all').cuda().eval()
    return xrv.models.DenseNet(weights='densenet121-res224-all').cuda().eval()


def _cache(variante):
    import numpy as np
    if variante == 'resnet512':
        return np.load(DATOS / 'cache512_X.npy', mmap_mode='r'), dict(np.load(DATOS / 'cache512_meta.npz'))
    nombre = {'base224': 'cache.npz', 'recorte': 'cache_pulmones_recorte.npz', 'mascara': 'cache_pulmones_mascara.npz'}[variante]
    c = dict(np.load(DATOS / nombre))
    return c.pop('X'), c


def salidas(variante):
    """S (N x 18, orden default_pathologies, NaN si no entrenada) y F (características), con caché en disco."""
    import numpy as np
    import torch
    import torchxrayvision as xrv
    archivo = DATOS / f'salidas_{variante}.npz'
    if archivo.exists():
        return dict(np.load(archivo))
    X, meta = _cache(variante)
    m = _modelo(variante)
    etiquetas = list(xrv.datasets.default_pathologies)
    th = getattr(m, 'op_threshs', None)
    columnas = [(etiquetas.index(t), j) for j, t in enumerate(m.targets)
                if t in etiquetas and not (th is not None and math.isnan(float(th[j])))]
    S, F = [], []
    lote = 16 if variante == 'resnet512' else 128
    with torch.inference_mode(), torch.autocast('cuda', dtype=torch.float16):
        for i in range(0, len(X), lote):
            x = torch.from_numpy(np.asarray(X[i:i + lote], dtype=np.float32)).unsqueeze(1).cuda()
            o = m(x).float().cpu().numpy()
            s = np.full((len(o), len(etiquetas)), np.nan)
            for k, j in columnas:
                s[:, k] = o[:, j]
            S.append(s)
            f = m.features(x) if variante == 'resnet512' else caracteristicas(m, x)
            F.append(f.float().cpu().numpy())
            if (i // lote) % 100 == 0:
                print(variante, i, flush=True)
    datos = {'S': np.concatenate(S), 'F': np.concatenate(F), **{k: meta[k] for k in ('tb', 'sitio', 'particion', 'clase')}}
    np.savez(archivo, **datos)
    return datos


def _logistica(C):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000, class_weight='balanced'))


def evaluar(S, F, y, sitio, part, clase):
    import numpy as np
    S = S[:, ~np.isnan(S).all(0)]
    S = np.where(np.isnan(S), np.nanmean(S, 0), S)
    sz = np.where(sitio == 'shenzhen')[0]
    tr = np.where((sitio == 'tbx11k') & (part == 'train'))[0]
    va = np.where((sitio == 'tbx11k') & (part == 'val'))[0]
    ext = {s: np.where(sitio == s)[0] for s in ('shenzhen', 'montgomery', 'dadb')}
    r = {}
    ind = _logistica(0.1).fit(S[sz], y[sz]).decision_function(S)
    r['indice'] = {'tbx11k_val': auc(y[va], ind[va]), **{s: auc(y[i], ind[i]) for s, i in ext.items() if s != 'shenzhen'}}
    pat = _logistica(0.1).fit(S[tr], y[tr]).decision_function(S)
    neg = np.sort(pat[va][y[va] == 0])
    corte = neg[int(np.ceil(0.9 * len(neg))) - 1]
    r['patron'] = {s: auc(y[i], pat[i]) for s, i in ext.items()}
    enf = va[np.isin(clase[va], ['tb', 'enfermo_no_tb'])]
    r['patron']['tb_vs_otra_enf'] = auc(y[enf], pat[enf])
    r['aviso'] = {s: [float((pat[i][y[i] == 1] >= corte).mean()), float((pat[i][y[i] == 0] >= corte).mean())]
                  for s, i in ext.items()}
    if F is not None:
        cab = _logistica(0.01).fit(F[tr], y[tr]).decision_function(F)
        r['cabeza_caract'] = {s: auc(y[i], cab[i]) for s, i in ext.items()}
    loso = {'s18': {}, 'caract': {}}
    for s in SITIOS:
        fuera, dentro = np.where(sitio == s)[0], np.where(sitio != s)[0]
        loso['s18'][s] = auc(y[fuera], _logistica(0.1).fit(S[dentro], y[dentro]).decision_function(S[fuera]))
        if F is not None:
            loso['caract'][s] = auc(y[fuera], _logistica(0.01).fit(F[dentro], y[dentro]).decision_function(F[fuera]))
    for k in list(loso):
        if loso[k]:
            loso[k]['media'] = float(np.mean(list(loso[k].values())))
        else:
            loso.pop(k)
    r['loso'] = loso
    return r


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variantes', default='base224,recorte,mascara,resnet512')
    parser.add_argument('--combinar', default='', help='grupos separados por coma, variantes unidas con +')
    args = parser.parse_args()
    import numpy as np
    resultados = {'validacion_clinica': False}
    cache = {}
    for v in [v for v in args.variantes.split(',') if v]:
        cache[v] = salidas(v)
        d = cache[v]
        resultados[v] = evaluar(d['S'], d['F'], d['tb'].astype(int), d['sitio'], d['particion'], d['clase'])
        print(v, json.dumps(resultados[v]), flush=True)
    for grupo in [g for g in args.combinar.split(',') if g]:
        partes = [cache.get(v) or salidas(v) for v in grupo.split('+')]
        with np.errstate(all='ignore'):
            S = np.nanmean(np.stack([p['S'] for p in partes]), 0)
        d = partes[0]
        resultados[grupo] = evaluar(S, None, d['tb'].astype(int), d['sitio'], d['particion'], d['clase'])
        print(grupo, json.dumps(resultados[grupo]), flush=True)
    previo = DATOS / 'resultados_variantes.json'
    todos = json.loads(previo.read_text(encoding='utf-8')) if previo.exists() else {}
    todos.update(resultados)
    previo.write_text(json.dumps(todos, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
