"""¿Combinar varios modelos XRV resiste mejor el cambio de hospital? NO es validación clínica.

Calcula las 18 salidas de cada DenseNet XRV de 224 px (all, nih, pc, chex, rsna, mimic_nb, mimic_ch) sobre la
caché con preprocesamiento de producción y compara, con el mismo protocolo de 2026-11-20:
- Índice (anormalidad): logística L2 de 18 salidas ajustada SOLO en Shenzhen (como indice_pulmonar_v1);
  prueba en Montgomery, DA+DB y TBX11K val (TB vs todo).
- Patrón TB: logística L2 ajustada SOLO en TBX11K train (TB vs todo); prueba en Shenzhen, Montgomery, DA+DB;
  aviso al corte de especificidad 90 % en TBX11K val.
Para cada categoría, el ensamble promedia solo los modelos entrenados en ella.
Uso (desde backend/, con .venv-gpu): python -m scripts.evaluacion_radiologia.tb_ensamble [--modelos all,nih,...]
"""
import argparse
import json

from scripts.evaluacion_radiologia.tb_entrenar import BASE_DIR, auc_ic

PESOS = ('all', 'nih', 'pc', 'chex', 'rsna', 'mimic_nb', 'mimic_ch')


def salidas(nombre, X):
    """Salidas (N x 18 en el orden por defecto de XRV) con NaN en categorías no entrenadas."""
    import numpy as np
    import torch
    import torchxrayvision as xrv
    modelo = xrv.models.DenseNet(weights=f'densenet121-res224-{nombre}').cuda().eval()
    validas = np.array([bool(t) for t in modelo.targets])
    if getattr(modelo, 'op_threshs', None) is not None:
        validas &= ~np.isnan(modelo.op_threshs.cpu().numpy())
    out = []
    with torch.inference_mode():
        for i in range(0, len(X), 128):
            x = torch.from_numpy(X[i:i + 128].astype(np.float32)).unsqueeze(1).cuda()
            out.append(modelo(x).float().cpu().numpy())
    S = np.concatenate(out)
    S[:, ~validas] = np.nan
    return S, list(modelo.targets), validas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelos', default=','.join(PESOS))
    args = parser.parse_args()
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    base = BASE_DIR / '.datasets/tb-entrenamiento'
    cache = base / 'salidas_ensamble.npz'
    previas = dict(np.load(cache)) if cache.exists() else {}
    c = np.load(base / 'cache.npz')
    y, sitio, part, clase = c['tb'].astype(int), c['sitio'], c['particion'], c['clase']
    import torchxrayvision as xrv
    etiquetas = list(xrv.datasets.default_pathologies)
    for nombre in args.modelos.split(','):
        if f'S_{nombre}' not in previas:
            S, targets, _ = salidas(nombre, c['X'])
            alineado = np.full((len(y), len(etiquetas)), np.nan)
            for j, t in enumerate(targets):
                if t in etiquetas:
                    alineado[:, etiquetas.index(t)] = S[:, j]
            previas[f'S_{nombre}'] = alineado
            np.savez(cache, **previas)
            print('listo', nombre, int((~np.isnan(alineado[0])).sum()), 'categorías', flush=True)

    sz = np.where(sitio == 'shenzhen')[0]
    tr = np.where((sitio == 'tbx11k') & (part == 'train'))[0]
    va = np.where((sitio == 'tbx11k') & (part == 'val'))[0]
    externos = {s: np.where(sitio == s)[0] for s in ('shenzhen', 'montgomery', 'dadb')}

    def evaluar(S):
        cols = ~np.isnan(S).all(0)
        S = np.nan_to_num(S[:, cols], nan=np.nanmean(S[:, cols]))
        def ajustar(filas):
            m, d = S[filas].mean(0), S[filas].std(0) + 1e-6
            lr = LogisticRegression(C=0.1, max_iter=5000, class_weight='balanced').fit((S[filas] - m) / d, y[filas])
            return lr.decision_function((S - m) / d)
        ind = ajustar(sz)
        r = {'categorias': int(cols.sum()),
             'indice_auc': {'tbx11k_val': auc_ic(y[va], ind[va])[0],
                            **{s: auc_ic(y[i], ind[i])[0] for s, i in externos.items() if s != 'shenzhen'}}}
        pat = ajustar(tr)
        neg = np.sort(pat[va][y[va] == 0])
        corte = neg[int(np.ceil(0.9 * len(neg))) - 1]
        r['patron_auc'] = {'tbx11k_val': auc_ic(y[va], pat[va])[0], **{s: auc_ic(y[i], pat[i])[0] for s, i in externos.items()}}
        r['patron_aviso'] = {s: {'tb': float((pat[i][y[i] == 1] >= corte).mean()), 'sana': float((pat[i][y[i] == 0] >= corte).mean())}
                             for s, i in externos.items()}
        enf = va[np.isin(clase[va], ['tb', 'enfermo_no_tb'])]
        r['patron_tb_vs_otra_enf'] = auc_ic(y[enf], pat[enf])[0]
        return r

    nombres = args.modelos.split(',')
    resultados = {'validacion_clinica': False}
    for n in nombres:
        resultados[n] = evaluar(previas[f'S_{n}'])
    pila = np.stack([previas[f'S_{n}'] for n in nombres])
    with np.errstate(all='ignore'):
        resultados['ensamble_' + '+'.join(nombres)] = evaluar(np.nanmean(pila, 0))
        sin_all = [n for n in nombres if n != 'all']
        if len(sin_all) > 1:
            resultados['ensamble_especialistas'] = evaluar(np.nanmean(np.stack([previas[f'S_{n}'] for n in sin_all]), 0))
    (base / 'resultados_ensamble.json').write_text(json.dumps(resultados, indent=1), encoding='utf-8')
    for k, v in resultados.items():
        if isinstance(v, dict):
            print(f"{k:28s} cat={v['categorias']:2d} | ÍNDICE " + ' '.join(f"{s[:5]}={a:.3f}" for s, a in v['indice_auc'].items())
                  + ' | PATRÓN ' + ' '.join(f"{s[:5]}={a:.3f}" for s, a in v['patron_auc'].items())
                  + f" otraEnf={v['patron_tb_vs_otra_enf']:.3f} | AVISO " +
                  ' '.join(f"{s[:5]} {a['tb']:.0%}/{a['sana']:.0%}" for s, a in v['patron_aviso'].items()))


if __name__ == '__main__':
    main()
