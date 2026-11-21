"""Exporta patron_tb_v1.json: "¿la imagen tiene un patrón compatible con TB?". NO es validación clínica.

Logística L2 sobre las 18 salidas XRV (mismo formato que indice_pulmonar_v1.json, sin pesos nuevos).
Entrena SOLO con TBX11K train: TB vs TODO lo demás (sanos + enfermos no TB).
Descartado (2026-11-20): entrenar solo TB vs enfermos-no-TB; ante placas sanas marcaba TB en 52-84 %.
Corte 'compatible' fijado en TBX11K val = especificidad 90 % frente a todo lo no TB. Externos solo se informan.
Uso (desde backend/, con .venv-gpu, tras tb_loso): python -m scripts.evaluacion_radiologia.tb_patron
"""
import json
from datetime import date

from scripts.evaluacion_radiologia.tb_entrenar import BASE_DIR, auc_ic, operar

C = 0.1
SALIDA = BASE_DIR / 'app/imagenes/infrastructure/vision/patron_tb_v1.json'


def main():
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    base = BASE_DIR / '.datasets/tb-entrenamiento'
    d = np.load(base / 'caracteristicas.npz')
    part = np.load(base / 'cache.npz')['particion']
    indice = json.loads((BASE_DIR / 'app/imagenes/infrastructure/vision/indice_pulmonar_v1.json').read_text(encoding='utf-8'))
    etiquetas = indice['etiquetas']
    S = d['S'][:, [list(d['targets']).index(e) for e in etiquetas]].astype(np.float64)
    y, sitio, clase = d['tb'].astype(int), d['sitio'], d['clase']
    tr = np.where((sitio == 'tbx11k') & (part == 'train'))[0]
    va = np.where((sitio == 'tbx11k') & (part == 'val'))[0]

    media, desv = S[tr].mean(0), S[tr].std(0) + 1e-6
    modelo = LogisticRegression(C=C, max_iter=5000, class_weight='balanced').fit((S[tr] - media) / desv, y[tr])
    coef, intercepto = modelo.coef_[0], float(modelo.intercept_[0])

    def valor(X):
        return 1 / (1 + np.exp(-(((X - media) / desv) @ coef + intercepto)))

    v = valor(S)
    negativos = np.sort(v[va][y[va] == 0])
    compatible = float(negativos[int(np.ceil(0.9 * len(negativos))) - 1])
    enf = va[np.isin(clase[va], ['tb', 'enfermo_no_tb'])]
    metricas = {'tbx11k_val': {'auc_ic95': auc_ic(y[va], v[va]), **operar(y[va], v[va], compatible),
                               'tb_vs_enfermo_no_tb_auc_ic95': auc_ic(y[enf], v[enf]),
                               'aviso_en_enfermo_no_tb': float((v[va][clase[va] == 'enfermo_no_tb'] >= compatible).mean()),
                               'aviso_en_sanos': float((v[va][clase[va] == 'sano'] >= compatible).mean())}}
    for s in ('shenzhen', 'montgomery', 'dadb'):
        idx = np.where(sitio == s)[0]
        metricas[s] = {'auc_ic95': auc_ic(y[idx], v[idx]), **operar(y[idx], v[idx], compatible)}
    artefacto = {'version': 'patron-tb-v1', 'fecha': date.today().isoformat(),
                 'modelo_base': indice['modelo_base'], 'etiquetas': etiquetas,
                 'coeficientes': coef.tolist(), 'media': media.tolist(), 'desviacion': desv.tolist(),
                 'intercepto': intercepto, 'umbrales': {'compatible': compatible},
                 'entrenamiento': 'TBX11K train (Liu et al., CVPR 2020; CC BY 4.0): TB vs sanos + enfermos no TB; logística L2 C=0.1',
                 'metricas': metricas,
                 'limites': 'El corte no se transfiere entre hospitales: en externos detecta 29-91 % de TB y marca 6-24 % de '
                            'sanos. Solo avisa, nunca descarta. Calibrar con casos locales; confirmar con VinDr-CXR.'}
    SALIDA.write_text(json.dumps(artefacto, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'umbrales': artefacto['umbrales'], 'metricas': metricas}, indent=1))


if __name__ == '__main__':
    main()
