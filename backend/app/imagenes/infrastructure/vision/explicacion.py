"""Explicabilidad y control de calidad del análisis visual (experimental, no diagnóstico).

- Mapas de calor Grad-CAM sobre la última capa convolucional del DenseNet XRV.
- Control de calidad de entrada a partir de metadatos y estadísticas del tensor.
Torch se importa solo dentro de `mapas_calor` (lo llama el trabajador efímero).
"""
import base64
from io import BytesIO

LATERALES = {'LL', 'RL', 'LAT', 'LATERAL', 'LLD', 'RLD'}
PARTES_TORAX = {'CHEST', 'THORAX', 'TORAX', 'TÓRAX', 'LUNG', 'PULMON'}
MODALIDADES_RX = {'CR', 'DX', 'DR'}


def evaluar_calidad(info: dict, desviacion: float, fraccion_saturada: float, proyeccion: str) -> dict:
    """Avisos de calidad. `desviacion` y `fraccion_saturada` se miden en el tensor XRV [-1024, 1024]."""
    avisos = []
    ancho, alto = info.get('original_size') or [0, 0]
    if min(ancho, alto) < 1000:
        avisos.append('Resolución baja (menos de 1000 px): puede ser una foto de pantalla o una copia reducida.')
    if desviacion < 150:
        avisos.append('Contraste muy bajo: revisa la exposición o la exportación de la imagen.')
    if fraccion_saturada > 0.35:
        avisos.append('Gran parte de la imagen está saturada (blanco o negro puro): posible sobre o subexposición.')
    dicom = info.get('dicom') or {}
    vista, parte, modalidad = dicom.get('view_position'), dicom.get('body_part'), dicom.get('modality')
    if vista in LATERALES:
        avisos.append('El DICOM indica proyección lateral: el modelo solo está preparado para tórax frontal.')
    elif vista in ('PA', 'AP') and proyeccion in ('PA', 'AP') and vista != proyeccion:
        avisos.append(f'La proyección declarada ({proyeccion}) no coincide con la del DICOM ({vista}).')
    if parte and parte not in PARTES_TORAX:
        avisos.append(f'El DICOM indica otra región anatómica ({parte}); el modelo es solo para tórax.')
    if modalidad and modalidad not in MODALIDADES_RX:
        avisos.append(f'Modalidad DICOM {modalidad}: el modelo está preparado para radiografía (CR/DX).')
    return {'estado': 'revisar' if avisos else 'ok', 'avisos': avisos,
            'medidas': {'desviacion_tensor': round(desviacion, 1), 'fraccion_saturada': round(fraccion_saturada, 3)}}


FRACCION_PULMONAR_MINIMA = 0.12


def agregar_aviso_pulmonar(calidad: dict, fraccion: float) -> dict:
    """Con segmentación: si casi no hay campos pulmonares, probablemente no es un tórax frontal."""
    calidad.setdefault('medidas', {})['fraccion_pulmonar'] = round(fraccion, 3)
    if fraccion < FRACCION_PULMONAR_MINIMA:
        calidad['avisos'].append('Casi no se detectan campos pulmonares: puede no ser una radiografía de tórax frontal o estar muy recortada.')
        calidad['estado'] = 'revisar'
    return calidad


def region_del_mapa(working_size: list[int]) -> dict:
    """XRayCenterCrop recorta el cuadrado central: el mapa 224x224 cubre esta región (normalizada)."""
    ancho, alto = working_size
    lado = min(ancho, alto)
    return {'x': (ancho - lado) / 2 / ancho, 'y': (alto - lado) / 2 / alto, 'ancho': lado / ancho, 'alto': lado / alto}


def _colorear_png(mapa) -> str:
    """Mapa [0,1] 224x224 -> PNG RGBA base64; transparente donde la activación es baja."""
    import numpy as np
    from PIL import Image
    v = np.clip(mapa, 0, 1)
    rojo = np.clip(1.5 * v, 0, 1)
    verde = np.clip(1.5 - np.abs(2.2 * v - 1.4) * 1.5, 0, 1)
    azul = np.clip(1.2 - 2.4 * v, 0, 1)
    alfa = np.clip((v - 0.2) / 0.8, 0, 1) ** 0.8
    rgba = (np.stack([rojo, verde, azul, alfa], axis=-1) * 255).round().astype(np.uint8)
    salida = BytesIO()
    Image.fromarray(rgba).save(salida, format='PNG', optimize=True)
    return base64.b64encode(salida.getvalue()).decode('ascii')


def zona_activa(mapa, umbral: float = 0.6) -> dict | None:
    """Caja (normalizada al mapa) del componente conexo que contiene el máximo de activación."""
    import numpy as np
    from scipy import ndimage
    if not np.isfinite(mapa).all() or mapa.max() <= 0:
        return None
    etiquetas, _ = ndimage.label(mapa >= umbral * mapa.max())
    pico = np.unravel_index(int(np.argmax(mapa)), mapa.shape)
    filas, columnas = np.nonzero(etiquetas == etiquetas[pico])
    alto, ancho = mapa.shape
    return {'x': float(columnas.min() / ancho), 'y': float(filas.min() / alto),
            'ancho': float((columnas.max() + 1 - columnas.min()) / ancho),
            'alto': float((filas.max() + 1 - filas.min()) / alto),
            'pico': {'x': float((pico[1] + 0.5) / ancho), 'y': float((pico[0] + 0.5) / alto)}}


def mapas_calor(modelo, tensor, objetivos: dict, mascara=None) -> dict:
    """Grad-CAM. `objetivos`: nombre -> función(salida_modelo[0]) -> escalar diferenciable.
    `mascara` (224x224, opcional): limita el mapa a los campos pulmonares antes de normalizar."""
    import numpy as np
    import torch
    import torch.nn.functional as F
    capturado = {}

    def guardar(_modulo, _entrada, salida):
        # XRV aplica relu(inplace=True) después: se devuelve una copia para conservar la activación.
        capturado['activacion'] = salida
        return salida.clone()
    gancho = modelo.features.register_forward_hook(guardar)
    try:
        with torch.enable_grad():
            entrada = tensor.clone().requires_grad_(False)
            salida = modelo(entrada)[0]
            activacion = capturado['activacion']
            resultado = {}
            nombres = list(objetivos)
            for i, nombre in enumerate(nombres):
                objetivo = objetivos[nombre](salida)
                (gradiente,) = torch.autograd.grad(objetivo, activacion, retain_graph=i < len(nombres) - 1)
                pesos = gradiente.mean(dim=(2, 3), keepdim=True)
                cam = F.relu((pesos * activacion).sum(dim=1, keepdim=True))
                cam = F.interpolate(cam, size=tensor.shape[-2:], mode='bilinear', align_corners=False)[0, 0]
                cam = cam.detach().numpy().astype(np.float32)
                if mascara is not None:
                    cam = cam * mascara
                cam = cam / cam.max() if cam.max() > 0 else cam
                resultado[nombre] = {'png_base64': _colorear_png(cam), 'zona': zona_activa(cam)}
    finally:
        gancho.remove()
    return resultado
