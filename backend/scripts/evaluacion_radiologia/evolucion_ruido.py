"""¿Cuánto cambian los números del asistente solo por repetir la toma? NO es validación clínica.

Para comparar una radiografía con la anterior del mismo paciente hace falta saber qué diferencia es "ruido de
toma" (paciente algo girado, más cerca, otro brillo) y qué diferencia vale la pena señalar.
Método: cada imagen externa de la caché (preprocesamiento de producción) se re-toma 2 veces con perturbaciones
pequeñas e independientes (rotación ±5°, escala ±5 %, desplazamiento ±3 %, gamma 0,85-1,15) y se mide la
diferencia absoluta entre ambas tomas en: índice pulmonar v1, patrón TB v1 (modelo base), patrón TB v2 (ensamble
de 7) y cada una de las 18 categorías. Tolerancia = percentil 95: el 95 % de las re-tomas cambia menos que eso.
Limitación: es una simulación; no hay pares reales de un mismo paciente en estos datos.
Uso (desde backend/, con .venv-gpu): python -m scripts.evaluacion_radiologia.evolucion_ruido
"""
import argparse
import json
import math
from datetime import date

from scripts.evaluacion_radiologia.tb_entrenar import BASE_DIR

VISION = BASE_DIR / 'app/imagenes/infrastructure/vision'
MODELOS = ('all', 'nih', 'pc', 'chex', 'rsna', 'mimic_nb', 'mimic_ch')


def retomar(x, generador):
    """Re-toma simulada de un lote (N,1,224,224) en la escala de producción [-1024, 1024]."""
    import torch
    import torch.nn.functional as F
    n = x.shape[0]
    u = lambda a: (torch.rand(n, generator=generador, device='cpu') * 2 - 1).to(x.device) * a
    ang, esc = u(math.radians(5)), 1 + u(0.05)
    tx, ty = u(0.06), u(0.06)  # ±3 % del ancho (la grilla va de -1 a 1)
    cos, sin = torch.cos(ang) / esc, torch.sin(ang) / esc
    theta = torch.stack([torch.stack([cos, -sin, tx], 1), torch.stack([sin, cos, ty], 1)], 1)
    grilla = F.affine_grid(theta, x.shape, align_corners=False)
    y = F.grid_sample(x, grilla, padding_mode='border', align_corners=False)
    gamma = (1 + u(0.15)).view(n, 1, 1, 1)
    y01 = ((y + 1024) / 2048).clamp(0, 1) ** gamma
    return y01 * 2048 - 1024


def logistica(S, a):
    """S: (N, 18) en el orden de a['etiquetas'] -> valor 0-1 (igual que calcular_indice / calcular_patron_tb)."""
    import numpy as np
    z = a['intercepto'] + ((S - np.array(a['media'])) / np.array(a['desviacion'])) @ np.array(a['coeficientes'])
    return 1 / (1 + np.exp(-z))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeticiones', type=int, default=2)
    parser.add_argument('--semilla', type=int, default=0)
    args = parser.parse_args()
    import numpy as np
    import torch
    import torchxrayvision as xrv
    c = np.load(BASE_DIR / '.datasets/tb-entrenamiento/cache.npz')
    sitio, part = c['sitio'], c['particion']
    filas = np.where((sitio != 'tbx11k') | (part == 'val'))[0]  # externos + validación (nunca entrenamiento)
    X = c['X'][filas]
    indice = json.loads((VISION / 'indice_pulmonar_v1.json').read_text(encoding='utf-8'))
    v1 = json.loads((VISION / 'patron_tb_v1.json').read_text(encoding='utf-8'))
    v2 = json.loads((VISION / 'patron_tb_v2.json').read_text(encoding='utf-8'))
    etiquetas = indice['etiquetas']
    assert v1['etiquetas'] == etiquetas == v2['etiquetas']
    modelos = {}
    for nombre in MODELOS:
        m = xrv.models.DenseNet(weights=f'densenet121-res224-{nombre}').cuda().eval()
        validas = [bool(t) and not (m.op_threshs is not None and math.isnan(float(m.op_threshs[j])))
                   for j, t in enumerate(m.targets)]
        columnas = [(etiquetas.index(t), j) for j, t in enumerate(m.targets) if validas[j] and t in etiquetas]
        modelos[nombre] = (m, columnas)

    def puntuar(lote):
        salida = {}
        with torch.inference_mode():
            for nombre, (m, columnas) in modelos.items():
                o = m(lote).float().cpu().numpy()
                S = np.full((len(o), len(etiquetas)), np.nan)
                for k, j in columnas:
                    S[:, k] = o[:, j]
                salida[nombre] = S
        return salida

    gen = torch.Generator().manual_seed(args.semilla)
    deltas = {'indice': [], 'patron_tb_v1': [], 'patron_tb_v2': [], 'categorias': []}
    cambios = {'nivel_prioridad': [], 'aviso_tb_v2': []}
    alta, media = indice['umbrales_provisionales']['alta'], indice['umbrales_provisionales']['media']
    nivel = lambda v: np.digitize(v, [media, alta])
    for _ in range(args.repeticiones):
        for i in range(0, len(X), 64):
            x = torch.from_numpy(X[i:i + 64].astype(np.float32)).unsqueeze(1).cuda()
            tomas = []
            for _ in range(2):
                S = puntuar(retomar(x, gen))
                with np.errstate(all='ignore'):
                    ens = np.nanmean(np.stack([S[n] for n in MODELOS]), 0)
                tomas.append({'base': S['all'], 'indice': logistica(S['all'], indice),
                              'patron_tb_v1': logistica(S['all'], v1), 'patron_tb_v2': logistica(ens, v2)})
            a, b = tomas
            for k in ('indice', 'patron_tb_v1', 'patron_tb_v2'):
                deltas[k].append(np.abs(a[k] - b[k]))
            deltas['categorias'].append(np.abs(a['base'] - b['base']))
            cambios['nivel_prioridad'].append(nivel(a['indice']) != nivel(b['indice']))
            u2 = v2['umbrales']['compatible']
            cambios['aviso_tb_v2'].append((a['patron_tb_v2'] >= u2) != (b['patron_tb_v2'] >= u2))
        print('repetición lista', flush=True)
    d = {k: np.concatenate(v) for k, v in deltas.items()}
    pct = lambda v: {'p50': float(np.percentile(v, 50)), 'p90': float(np.percentile(v, 90)), 'p95': float(np.percentile(v, 95))}

    # Para dar escala: diferencia típica entre una placa con TB y una sana (mismo índice, sin re-toma).
    S0 = np.concatenate([puntuar(torch.from_numpy(X[i:i + 64].astype(np.float32)).unsqueeze(1).cuda())['all']
                         for i in range(0, len(X), 64)])
    ind0, y = logistica(S0, indice), c['tb'][filas]
    escala = float(np.median(ind0[y == 1]) - np.median(ind0[y == 0]))
    salida = {
        'version': 'evolucion-v1', 'fecha': date.today().isoformat(), 'validacion_clinica': False,
        'metodo': 'Dos re-tomas simuladas por imagen (rotación ±5°, escala ±5 %, desplazamiento ±3 %, gamma 0,85-1,15) '
                  f'sobre {len(X)} radiografías externas/validación (Shenzhen, Montgomery, India, TBX11K val), '
                  f'{args.repeticiones} repeticiones. Tolerancia = percentil 95 de la diferencia absoluta entre re-tomas.',
        'tolerancias': {'indice': pct(d['indice'])['p95'], 'patron_tb_v1': pct(d['patron_tb_v1'])['p95'],
                        'patron_tb_v2': pct(d['patron_tb_v2'])['p95'],
                        'categorias': {e: float(np.percentile(d['categorias'][:, k], 95)) for k, e in enumerate(etiquetas)}},
        'metricas': {'indice': pct(d['indice']), 'patron_tb_v1': pct(d['patron_tb_v1']), 'patron_tb_v2': pct(d['patron_tb_v2']),
                     'cambia_nivel_prioridad_por_retoma': float(np.concatenate(cambios['nivel_prioridad']).mean()),
                     'cambia_aviso_tb_v2_por_retoma': float(np.concatenate(cambios['aviso_tb_v2']).mean()),
                     'diferencia_mediana_indice_tb_vs_sin_tb': escala},
        'limites': 'Simulación: no hay pares reales del mismo paciente. Cambios de equipo, proyección (AP/PA) o '
                   'inspiración pueden mover más los números. Un cambio dentro de la tolerancia no significa "igual": '
                   'el médico compara las imágenes.',
    }
    (VISION / 'evolucion_v1.json').write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: salida[k] for k in ('tolerancias', 'metricas')}, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
