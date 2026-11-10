import asyncio
import hashlib

from app.imagenes.application.fusionar_hallazgos import fusionar
from app.imagenes.domain.vision import ErrorVision


def validar_snapshot(trabajo: dict, snapshot: dict | None):
    if (not snapshot or not snapshot.get('archivo')
            or snapshot['id'] != trabajo['estudio_id']
            or snapshot['informe_id'] != trabajo['informe_id']
            or snapshot['archivo']['id'] != trabajo['archivo_id']
            or snapshot['archivo']['hash_sha256'] != trabajo['archivo_sha256']
            or hashlib.sha256(snapshot['informe_texto'].encode()).hexdigest() != trabajo['informe_sha256']):
        raise ValueError('El estudio, informe o archivo cambió; solicita otro análisis.')


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
        # No convertir scores a diagnósticos: consulta documental de las tres categorías.
        pregunta = 'Radiografía de tórax: consolidación pulmonar, derrame pleural y cardiomegalia. Hallazgos radiográficos.'
        try:
            evidencia = await self.rag.consultar(pregunta)
        except Exception:
            # El componente documental es opcional; incluso un fallo de su BD
            # no debe borrar una inferencia visual válida. Cancelación no se absorbe.
            evidencia = {'estado':'no_disponible','evidencia':[],
                'mensaje':'No se pudo consultar el corpus local; no se generó explicación sin evidencia.'}
        return {'experimental':True,'vision':visual,'fusion':combinado,'rag':evidencia}
