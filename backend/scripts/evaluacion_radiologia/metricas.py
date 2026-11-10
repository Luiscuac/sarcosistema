"""Métricas sin dependencias ML. None significa no evaluable, nunca negativo."""
from collections import Counter
import math


def dividir(a, b):
    return a / b if b else None


def clasificacion(referencia: list, prediccion: list) -> dict:
    if len(referencia) != len(prediccion):
        raise ValueError('Longitudes diferentes')
    pares = [(r, p) for r, p in zip(referencia, prediccion) if r is not None]
    clases = sorted({r for r, _ in pares} | {p for _, p in pares if p is not None})
    matriz = {r: {p: sum(a == r and b == p for a, b in pares) for p in clases} for r in clases}
    f1 = {}
    for c in clases:
        tp = sum(r == p == c for r, p in pares)
        fp = sum(r != c and p == c for r, p in pares)
        fn = sum(r == c and p != c for r, p in pares)
        f1[c] = dividir(2 * tp, 2 * tp + fp + fn)
    valores = [v for v in f1.values() if v is not None]
    return {'n_total': len(referencia), 'n_evaluable': len(pares),
        'excluidos': len(referencia) - len(pares),
        'exactitud': dividir(sum(r == p for r, p in pares), len(pares)),
        'macro_f1': dividir(sum(valores), len(valores)), 'f1_por_clase': f1, 'matriz': matriz,
        'soporte': dict(Counter(r for r, _ in pares))}


def binaria(referencia: list, scores: list, umbral: float = .5) -> dict:
    if len(referencia) != len(scores) or any(not math.isfinite(s) for s in scores):
        raise ValueError('Scores o longitudes inválidos')
    if any(r not in (0, 1, None) for r in referencia):
        raise ValueError('Referencia no binaria')
    pares = [(r, s) for r, s in zip(referencia, scores) if r is not None]
    positivos = [s for r, s in pares if r == 1]
    negativos = [s for r, s in pares if r == 0]
    tp = sum(r == 1 and s >= umbral for r, s in pares)
    fp = sum(r == 0 and s >= umbral for r, s in pares)
    tn = sum(r == 0 and s < umbral for r, s in pares)
    fn = sum(r == 1 and s < umbral for r, s in pares)
    auc = dividir(sum((a > b) + .5 * (a == b) for a in positivos for b in negativos), len(positivos) * len(negativos))
    # Average precision por grupos de empates, no orden arbitrario de filas.
    ap = 0.0
    for valor in sorted(set(positivos), reverse=True):
        ap += positivos.count(valor) * dividir(sum(r == 1 and s >= valor for r, s in pares), sum(s >= valor for _, s in pares))
    return {'n_total': len(referencia), 'n_evaluable': len(pares), 'excluidos': len(referencia)-len(pares),
        'positivos': len(positivos), 'negativos': len(negativos), 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
        'sensibilidad': dividir(tp, tp+fn), 'especificidad': dividir(tn, tn+fp),
        'precision': dividir(tp, tp+fp), 'f1': dividir(2*tp, 2*tp+fp+fn),
        'auroc': auc, 'ap': dividir(ap, len(positivos)), 'umbral_tecnico_no_clinico': umbral}
