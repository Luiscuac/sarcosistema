"""Triaje visual automático: resumen por estudio y nivel de prioridad (experimental).

El nivel ordena la revisión; no es diagnóstico. Los umbrales por defecto vienen del
artefacto del índice (fijados en Shenzhen) y deben calibrarse con casos del propio hospital.
"""

import asyncio

NIVELES = ('alta', 'media', 'baja')
ACTIVOS = ('en_cola', 'procesando')


def resumir_triaje(filas: list[dict]) -> dict[int, dict]:
    """filas: estudio_id, estado, indice, calidad, contribuciones, patron_tb (una por radiografía)."""
    resumen: dict[int, dict] = {}
    for f in filas:
        r = resumen.setdefault(f['estudio_id'], {'estado': None, 'indice': None, 'calidad': None,
                                                 'contribuciones': [], 'radiografias': 0, 'patron_tb': None})
        r['radiografias'] += 1
        if f.get('patron_tb') == 'compatible':
            r['patron_tb'] = 'compatible'
        if f['indice'] is not None and (r['indice'] is None or f['indice'] > r['indice']):
            r['indice'] = f['indice']
            r['contribuciones'] = list(f.get('contribuciones') or [])[:3]
        if f.get('calidad') == 'revisar' or (r['calidad'] is None and f.get('calidad')):
            r['calidad'] = f['calidad']
        estados = r.setdefault('_estados', set())
        estados.add(f['estado'])
    for r in resumen.values():
        estados = r.pop('_estados')
        if estados & set(ACTIVOS):
            r['estado'] = 'en_proceso'
        elif r['indice'] is not None:
            r['estado'] = 'completado'
        else:
            r['estado'] = 'error'
    return resumen


def nivel_prioridad(indice: float | None, umbral_alta: float, umbral_media: float) -> str | None:
    if indice is None:
        return None
    if indice >= umbral_alta:
        return 'alta'
    return 'media' if indice >= umbral_media else 'baja'


class TriarRadiografia:
    """Solo visión (sin informe ni RAG): prioridad visual apenas se sube la radiografía."""

    def __init__(self, vision, leer_archivo):
        self.vision = vision
        self.leer_archivo = leer_archivo

    async def ejecutar(self, archivo: dict) -> dict:
        contenido = await asyncio.to_thread(self.leer_archivo, archivo)
        visual = await asyncio.to_thread(self.vision.analizar, contenido, proyeccion='frontal_no_especificada')
        return {'experimental': True, 'tipo': 'triaje', **visual}


def umbrales_triaje() -> tuple[float, float]:
    """(alta, media) en uso: la configuración local si existe; si no, los provisionales del artefacto del índice."""
    from app.config.settings import settings
    from app.imagenes.infrastructure.vision.indice import cargar_indice
    provisional = cargar_indice()['umbrales_provisionales']
    alta, media = settings.radiology_triage_umbral_alta, settings.radiology_triage_umbral_media
    return (provisional['alta'] if alta is None else alta, provisional['media'] if media is None else media)
