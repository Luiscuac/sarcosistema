from app.imagenes.domain.ecografia import ORGANOS
from app.imagenes.domain.errors import EstudioNoEncontrado, InformeYaPublicado, SolicitudInvalida
from app.imagenes.application.ports.extractor_ecografia import ExtractorEcografia


class ExtraerHallazgosEcografia:
    def __init__(self, repositorio, extractor: ExtractorEcografia):
        self.repositorio = repositorio
        self.extractor = extractor

    async def ejecutar(self, estudio_id: int, transcripcion: str) -> dict:
        estudio = await self.repositorio.obtener_estudio(estudio_id)
        if estudio is None:
            raise EstudioNoEncontrado('El estudio no existe.')
        if estudio.tipo_estudio_codigo not in ORGANOS:
            raise SolicitudInvalida('El estudio no tiene una plantilla de ecografía compatible.')
        if estudio.informe is not None and estudio.informe.estado == 'publicado':
            raise InformeYaPublicado('El informe ya está publicado.')

        organos = ORGANOS[estudio.tipo_estudio_codigo]
        resultado = await self.extractor.extraer(transcripcion, organos)
        return resultado | {
            'modelo': self.extractor.modelo,
        }
