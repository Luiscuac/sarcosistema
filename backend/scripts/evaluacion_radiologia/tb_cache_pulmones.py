"""Cachés "solo pulmones" para cortar el atajo del hospital. NO es validación clínica.

Hipótesis (2026-11-21): el re-entrenamiento falló en hospitales externos porque el modelo reconoce el hospital por
bordes, letras, marcas y colimación. Si solo ve los pulmones, ese atajo se reduce.
A partir de cache.npz (preprocesamiento de producción) y la segmentación local PSPNet ChestX-Det (safetensors
verificado, la misma de los mapas de calor):
- recorte: rectángulo de los pulmones (máscara dilatada) + 4 % de margen, re-escalado a 224.
- mascara: lo mismo, y fuera de los pulmones dilatados se pone en negro (-1024).
Si la máscara cubre < 8 % de la imagen (segmentación fallida) se deja la imagen original y se cuenta.
Limitación: recorta sobre la versión de 224 px (al ampliar se pierde algo de detalle); producción podría recortar
sobre la imagen completa.
Uso (desde backend/, con .venv-gpu): python -m scripts.evaluacion_radiologia.tb_cache_pulmones
"""
import json

from scripts.evaluacion_radiologia.tb_entrenar import BASE_DIR


def main():
    import numpy as np
    import torch
    import torch.nn.functional as F
    import torchvision
    from app.imagenes.infrastructure.vision.segmentacion import PULMONES, cargar_segmentador
    base = BASE_DIR / '.datasets/tb-entrenamiento'
    c = dict(np.load(base / 'cache.npz'))
    X = c['X']
    seg = cargar_segmentador().cuda().eval()
    recorte = np.zeros_like(X)
    mascara = np.zeros_like(X)
    fallidas, areas = 0, []
    with torch.inference_mode():
        for i in range(0, len(X), 8):
            x = torch.from_numpy(X[i:i + 8].astype(np.float32)).unsqueeze(1).cuda()
            e = F.interpolate(x.repeat(1, 3, 1, 1), size=(512, 512), mode='bilinear', align_corners=False)
            e = torchvision.transforms.functional.normalize((e + 1024) / 2048, [0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            with torch.autocast("cuda", dtype=torch.float16):
                logits = seg(e).float()
            p = (torch.sigmoid(logits[:, list(PULMONES)]) > 0.5).any(1, keepdim=True).float()
            m = F.max_pool2d(F.interpolate(p, size=(224, 224), mode='nearest'), 15, 1, 7)
            for j in range(len(x)):
                mj = m[j, 0]
                area = float(mj.mean())
                areas.append(area)
                if area < 0.08:
                    fallidas += 1
                    recorte[i + j] = X[i + j]
                    mascara[i + j] = X[i + j]
                    continue
                filas, cols = torch.where(mj > 0)
                margen = 9  # ~4 % de 224
                r0, r1 = max(int(filas.min()) - margen, 0), min(int(filas.max()) + margen + 1, 224)
                c0, c1 = max(int(cols.min()) - margen, 0), min(int(cols.max()) + margen + 1, 224)
                xi = x[j:j + 1, :, r0:r1, c0:c1]
                mi = mj[r0:r1, c0:c1][None, None]
                a = F.interpolate(xi, size=(224, 224), mode='bilinear', align_corners=False)
                b = F.interpolate(xi * mi + (-1024) * (1 - mi), size=(224, 224), mode='bilinear', align_corners=False)
                recorte[i + j] = a[0, 0].clamp(-1024, 1024).cpu().numpy().astype(np.float16)
                mascara[i + j] = b[0, 0].clamp(-1024, 1024).cpu().numpy().astype(np.float16)
            if (i // 8) % 200 == 0:
                print(f'{i + len(x)}/{len(X)}', flush=True)
    meta = {k: v for k, v in c.items() if k != 'X'}
    np.savez(base / 'cache_pulmones_recorte.npz', X=recorte, **meta)
    np.savez(base / 'cache_pulmones_mascara.npz', X=mascara, **meta)
    info = {'imagenes': int(len(X)), 'segmentacion_fallida': fallidas,
            'area_pulmon_mediana': float(np.median(areas)),
            'fallidas_por_sitio': {s: int(sum(1 for k, a in enumerate(areas) if a < 0.08 and c['sitio'][k] == s))
                                   for s in np.unique(c['sitio'])}}
    (base / 'cache_pulmones_info.json').write_text(json.dumps(info, indent=1), encoding='utf-8')
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
