"""Detector experimental de TB sobre el DenseNet XRV de producción (GPU). NO es validación clínica.

Protocolo (evita el "examen ya estudiado"):
- Entrena SOLO con TBX11K train (China). Elige épocas/hiperparámetros SOLO con TBX11K val.
- Prueba externa, una vez y sin reajustar: Shenzhen (China, otro hospital), Montgomery (EE. UU.), DA+DB (India).
- El umbral se fija en TBX11K val (sensibilidad 90 %) y se aplica tal cual en los externos.
- Compara con la línea base de producción: índice pulmonar v1 (ojo: v1 se ajustó con Shenzhen).
- Mide aparte TB vs "enfermo pero no TB" en TBX11K val: que no marque TB ante cualquier anomalía.

Modos: lineal (backbone congelado), parcial (re-entrena denseblock4 + norm5), completo (todo, LR bajo).
Uso (desde backend/, con .venv-gpu): python -m scripts.evaluacion_radiologia.tb_entrenar --modo parcial
"""
import argparse
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SITIOS_EXTERNOS = ('shenzhen', 'montgomery', 'dadb')


def auc(y, s):
    import numpy as np
    y, s = np.asarray(y), np.asarray(s)
    p, q = s[y == 1], s[y == 0]
    return float(((p[:, None] > q[None, :]).sum() + .5 * (p[:, None] == q[None, :]).sum()) / (len(p) * len(q)))


def auc_ic(y, s, repeticiones=1000, semilla=0):
    import numpy as np
    y, s = np.asarray(y), np.asarray(s)
    rng = np.random.default_rng(semilla)
    p, q = s[y == 1], s[y == 0]
    r = []
    for _ in range(repeticiones):
        pp, qq = rng.choice(p, len(p)), rng.choice(q, len(q))
        r.append(((pp[:, None] > qq[None, :]).sum() + .5 * (pp[:, None] == qq[None, :]).sum()) / (len(pp) * len(qq)))
    return [auc(y, s), float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))]


def umbral_sensibilidad(y, s, objetivo=0.9):
    import numpy as np
    pos = np.sort(np.asarray(s)[np.asarray(y) == 1])
    return float(pos[int(np.floor((1 - objetivo) * len(pos)))])


def operar(y, s, u):
    import numpy as np
    y, s = np.asarray(y), np.asarray(s)
    return {'sensibilidad': float((s[y == 1] >= u).mean()), 'especificidad': float((s[y == 0] < u).mean())}


def cargar_modelo(dir_modelo: Path):
    import torch
    import torchxrayvision as xrv
    from safetensors.torch import load_file
    meta = json.loads((dir_modelo / 'manifest.json').read_text(encoding='utf-8'))
    pesos = next(dir_modelo.glob('*.safetensors'))
    modelo = xrv.models.DenseNet(weights=None, op_threshs=torch.tensor(meta['op_threshs']))
    modelo.load_state_dict(load_file(str(pesos), device='cpu'), strict=True)
    return modelo, meta['targets']


def caracteristicas(modelo, x):
    """Igual que XRV features2: features -> relu -> pool global (1024)."""
    import torch.nn.functional as F
    return F.adaptive_avg_pool2d(F.relu(modelo.features(x)), 1).flatten(1)


def aumentar(x):
    """Aumento suave en GPU: rotación ±10°, escala 0.9-1.1, desplazamiento 5 %, contraste ±10 %."""
    import math
    import torch
    import torch.nn.functional as F
    n = x.shape[0]
    ang = (torch.rand(n, device=x.device) * 2 - 1) * math.radians(10)
    esc = 1 + (torch.rand(n, device=x.device) * 2 - 1) * 0.1
    tx, ty = [(torch.rand(n, device=x.device) * 2 - 1) * 0.1 for _ in range(2)]
    cos, sin = torch.cos(ang) / esc, torch.sin(ang) / esc
    theta = torch.stack([torch.stack([cos, -sin, tx], 1), torch.stack([sin, cos, ty], 1)], 1)
    grid = F.affine_grid(theta, x.shape, align_corners=False)
    x = F.grid_sample(x, grid, padding_mode='border', align_corners=False)
    return x * (1 + (torch.rand(n, 1, 1, 1, device=x.device) * 2 - 1) * 0.1)


class Detector:
    """Backbone XRV (copia) + cabeza lineal de TB."""

    def __init__(self, modelo, modo):
        import torch
        self.modelo, self.modo = modelo, modo
        self.cabeza = torch.nn.Linear(1024, 1)
        for p in self.modelo.parameters():
            p.requires_grad = modo == 'completo'
        if modo == 'parcial':
            for nombre in ('denseblock4', 'norm5'):
                for p in getattr(self.modelo.features, nombre).parameters():
                    p.requires_grad = True

    def parametros(self, lr):
        grupos = [{'params': self.cabeza.parameters(), 'lr': lr}]
        cuerpo = [p for p in self.modelo.parameters() if p.requires_grad]
        if cuerpo:
            grupos.append({'params': cuerpo, 'lr': lr * (0.1 if self.modo == 'completo' else 0.3)})
        return grupos

    def to(self, d):
        self.modelo.to(d)
        self.cabeza.to(d)
        return self

    def entrenar(self, activo):
        self.modelo.train(activo and self.modo != 'lineal')
        if self.modo == 'parcial' and activo:
            self.modelo.eval()  # BN congelado salvo en el bloque re-entrenado
            self.modelo.features.denseblock4.train()
            self.modelo.features.norm5.train()
        self.cabeza.train(activo)

    def __call__(self, x):
        return self.cabeza(caracteristicas(self.modelo, x)).squeeze(1)


def predecir(fn, X, idx, lote=128):
    import numpy as np
    import torch
    salidas = []
    with torch.inference_mode(), torch.autocast('cuda', dtype=torch.float16):
        for i in range(0, len(idx), lote):
            x = torch.from_numpy(X[idx[i:i + lote]].astype(np.float32)).unsqueeze(1).cuda()
            salidas.append(fn(x).float().cpu())
    return torch.cat(salidas).numpy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modo', choices=('lineal', 'parcial', 'completo'), default='parcial')
    parser.add_argument('--epocas', type=int, default=15)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--lote', type=int, default=32)
    parser.add_argument('--semilla', type=int, default=0)
    parser.add_argument('--con-shenzhen', action='store_true',
                        help='Multi-sitio: suma 80 %% de Shenzhen al entreno y 20 %% a la validación; externos MC y DA+DB')
    parser.add_argument('--cache', type=Path, default=BASE_DIR / '.datasets/tb-entrenamiento/cache.npz')
    parser.add_argument('--modelos', type=Path, default=BASE_DIR / '.models/radiologia')
    parser.add_argument('--salida', type=Path, default=BASE_DIR / '.datasets/tb-entrenamiento')
    args = parser.parse_args()
    import numpy as np
    import torch
    torch.manual_seed(args.semilla)
    rng = np.random.default_rng(args.semilla)
    d = np.load(args.cache)
    X, y, sitio, part, clase = d['X'], d['tb'].astype(np.float32), d['sitio'], d['particion'], d['clase']
    tr = np.where((sitio == 'tbx11k') & (part == 'train'))[0]
    va = np.where((sitio == 'tbx11k') & (part == 'val'))[0]
    sz_va = np.array([], dtype=int)
    if args.con_shenzhen:
        sz = rng.permutation(np.where(sitio == 'shenzhen')[0])
        corte = int(len(sz) * 0.8)
        tr, sz_va = np.concatenate([tr, sz[:corte]]), np.sort(sz[corte:])
        va = np.concatenate([va, sz_va])

    modelo, targets = cargar_modelo(args.modelos)
    modelo = modelo.cuda().eval()
    # Línea base de producción: índice pulmonar v1 sobre las 18 salidas originales.
    art = json.loads((BASE_DIR / 'app/imagenes/infrastructure/vision/indice_pulmonar_v1.json').read_text(encoding='utf-8'))
    orden = [targets.index(e) for e in art['etiquetas']]
    w, m, s = (torch.tensor(art[k], device='cuda') for k in ('coeficientes', 'media', 'desviacion'))
    todos = np.arange(len(y))
    base = predecir(lambda x: ((modelo(x)[:, orden] - m) / s * w).sum(1) + art['intercepto'], X, todos)

    det = Detector(modelo, args.modo).to('cuda')
    opt = torch.optim.AdamW(det.parametros(args.lr), weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epocas)
    pos_weight = torch.tensor((y[tr] == 0).sum() / (y[tr] == 1).sum(), device='cuda')
    perdida_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    escalador = torch.amp.GradScaler('cuda')
    mejor, historial, estado = -1, [], None
    for epoca in range(args.epocas):
        inicio = time.perf_counter()
        det.entrenar(True)
        orden_tr = rng.permutation(tr)
        total = 0.0
        for i in range(0, len(orden_tr), args.lote):
            lote = orden_tr[i:i + args.lote]
            x = torch.from_numpy(X[lote].astype(np.float32)).unsqueeze(1).cuda()
            t = torch.from_numpy(y[lote]).cuda()
            with torch.autocast('cuda', dtype=torch.float16):
                perdida = perdida_fn(det(aumentar(x)), t)
            opt.zero_grad(set_to_none=True)
            escalador.scale(perdida).backward()
            escalador.step(opt)
            escalador.update()
            total += perdida.item() * len(lote)
        sched.step()
        det.entrenar(False)
        auc_va = auc(y[va], predecir(det, X, va))
        historial.append({'epoca': epoca + 1, 'perdida': total / len(tr), 'auc_val': auc_va,
                          'segundos': time.perf_counter() - inicio})
        print(json.dumps(historial[-1]), flush=True)
        if auc_va > mejor:
            mejor = auc_va
            estado = ({k: v.detach().cpu().clone() for k, v in det.modelo.state_dict().items()},
                      {k: v.detach().cpu().clone() for k, v in det.cabeza.state_dict().items()})
    det.modelo.load_state_dict(estado[0])
    det.cabeza.load_state_dict(estado[1])
    det.entrenar(False)
    pred = predecir(det, X, todos)

    u_det = umbral_sensibilidad(y[va], pred[va])
    u_base = umbral_sensibilidad(y[va], base[va])
    resultados = {'validacion_clinica': False, 'modo': args.modo, 'semilla': args.semilla, 'epocas': args.epocas,
                  'lr': args.lr, 'mejor_auc_val': mejor, 'historial': historial, 'sitios': {}}
    va_sick = va[np.isin(clase[va], ['tb', 'enfermo_no_tb'])]  # solo TBX11K tiene 'enfermo_no_tb'
    resultados['tbx11k_val_tb_vs_enfermo_no_tb'] = {'detector': auc_ic(y[va_sick], pred[va_sick]),
                                                    'indice_v1': auc_ic(y[va_sick], base[va_sick])}
    externos = [s_ for s_ in SITIOS_EXTERNOS if not (args.con_shenzhen and s_ == 'shenzhen')]
    evaluar = [('validacion', va)] + ([('shenzhen_val20', sz_va)] if args.con_shenzhen else [])
    for nombre, idx in evaluar + [(s_, np.where(sitio == s_)[0]) for s_ in externos]:
        resultados['sitios'][nombre] = {
            'n': int(len(idx)), 'tb': int(y[idx].sum()),
            'detector': {'auc_ic95': auc_ic(y[idx], pred[idx]), **operar(y[idx], pred[idx], u_det)},
            'indice_v1': {'auc_ic95': auc_ic(y[idx], base[idx]), **operar(y[idx], base[idx], u_base)}}
    args.salida.mkdir(parents=True, exist_ok=True)
    nombre = f"{args.modo}{'_multi' if args.con_shenzhen else ''}_s{args.semilla}"
    (args.salida / f'resultados_{nombre}.json').write_text(json.dumps(resultados, indent=1), encoding='utf-8')
    np.save(args.salida / f'pred_{nombre}.npy', pred)
    from safetensors.torch import save_file
    dir_pesos = BASE_DIR / '.models/tb-experimental'
    dir_pesos.mkdir(parents=True, exist_ok=True)
    save_file({**{f'modelo.{k}': v.contiguous() for k, v in estado[0].items()},
               **{f'cabeza.{k}': v.contiguous() for k, v in estado[1].items()}}, str(dir_pesos / f'{nombre}.safetensors'))
    print(json.dumps({k: v for k, v in resultados.items() if k != 'historial'}, indent=1))


if __name__ == '__main__':
    main()
