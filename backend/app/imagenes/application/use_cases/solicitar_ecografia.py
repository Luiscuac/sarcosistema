"""Caso de uso: el medico solicita una ecografia."""
from app.imagenes.domain.entities import SolicitudEcografia
from app.imagenes.domain.errors import SolicitudInvalida


class SolicitarEcografia:
    def __init__(self, repositorio):
        self.repositorio = repositorio

    async def ejecutar(self, solicitud: SolicitudEcografia, usuario_id: int) -> int:
        if not solicitud.tipo_estudio_ids:
            raise SolicitudInvalida('Selecciona al menos un estudio de imagen')
        if len(solicitud.tipo_estudio_ids) != len(set(solicitud.tipo_estudio_ids)):
            raise SolicitudInvalida('No repitas el mismo estudio en una solicitud')
        if not solicitud.medico_solicitante_nombre.strip():
            raise SolicitudInvalida('Registra el nombre del profesional solicitante')
        return await self.repositorio.crear_solicitud(solicitud, usuario_id)
