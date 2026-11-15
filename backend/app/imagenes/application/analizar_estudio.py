import asyncio
import hashlib

from app.imagenes.application.fusionar_hallazgos import fusionar
from app.imagenes.domain.vision import ErrorVision, NOMBRES_ES


def validar_snapshot(trabajo: dict, snapshot: dict | None):
    if (not snapshot or not snapshot.get('archivo')
            or snapshot['id'] != trabajo['estudio_id']
            or snapshot['informe_id'] != trabajo['informe_id']
            or snapshot['archivo']['id'] != trabajo['archivo_id']
            or snapshot['archivo']['hash_sha256'] != trabajo['archivo_sha256']
            or hashlib.sha256(snapshot['informe_texto'].encode()).hexdigest() != trabajo['informe_sha256']):
        raise ValueError('El estudio, informe o archivo cambió; solicita otro análisis.')


def pregunta_documental(visual: dict) -> str:
    aportes = (visual.get('indice_pulmonar') or {}).get('contribuciones') or []
    nombres = [NOMBRES_ES.get(c['name'], c['name']) for c in aportes[:3]]
    for fijo in ('consolidación pulmonar', 'derrame pleural', 'cardiomegalia'):
        if len(nombres) >= 3:
            break
        if not any(fijo.startswith(n) or n.startswith(fijo.split()[0]) for n in nombres):
            nombres.append(fijo)
    return f"Radiografía de tórax: {', '.join(nombres[:-1])} y {nombres[-1]}. Hallazgos radiográficos."


class AnalizarEstudio:
    def __init__(self, vision, rag, leer_archivo, umbral=0.5):
        self.vision = vision
        self.rag = rag
        self.leer_archivo = leer_archivo
        self.umbral = umbral

    async def ejecutar(self, trabajo, snapshot):
        validar_snapshot(trabajo,snapshot)
        contenido = await asyncio.to_thread(self.leer_archivo, snapshot['archivo'])
        visual = await asyncio.to_thread(self.vision.analizar, contenido, proyeccion=trabajo['proyeccion'])
        combinado = fusionar(visual,trabajo['informe_texto'],self.umbral)
        # No convertir scores a diagnósticos: consulta documental de las categorías que más pesan.
        pregunta = pregunta_documental(visual)
        try:
            evidencia = await self.rag.consultar(pregunta)
        except Exception:
            # El componente documental es opcional; incluso un fallo de su BD
            # no debe borrar una inferencia visual válida. Cancelación no se absorbe.
            evidencia = {'estado':'no_disponible','evidencia':[],
                'mensaje':'No se pudo consultar el corpus local; no se generó explicación sin evidencia.'}
        return {'experimental':True,'vision':visual,'fusion':combinado,'rag':evidencia}
