"""Puertos clínicos; paquete para convivir con el puerto de visión local."""
from typing import Protocol

from app.imagenes.domain.entities import (
    ArchivoImagen,
    EstudioImagenDetalle,
    EstudioImagenPendiente,
    EstudioImagenPublicado,
    InformeImagen,
    SolicitudEcografia,
)


class RepositorioImagen(Protocol):
    async def crear_solicitud(self, solicitud: SolicitudEcografia, usuario_id: int) -> int: ...

    async def listar_bandeja(self) -> list[EstudioImagenPendiente]: ...

    async def obtener_estudio(self, estudio_id: int) -> EstudioImagenDetalle | None: ...

    async def guardar_informe(
        self, estudio_id: int, descripcion: str | None, archivos: list[dict], usuario_id: int
    ) -> tuple[InformeImagen, bool]: ...

    async def publicar_informe(self, estudio_id: int, usuario_id: int) -> InformeImagen: ...

    async def listar_publicados_paciente(self, paciente_id: int) -> list[EstudioImagenPublicado]: ...

    async def obtener_archivo(self, archivo_id: int) -> ArchivoImagen | None: ...


class AlmacenImagen(Protocol):
    """Guarda el binario fuera de la BD y devuelve la ruta con que se referencia."""

    async def guardar(self, contenido: bytes, estudio_id: int, hash_sha256: str, extension: str) -> str: ...

    def ruta_absoluta(self, url_archivo: str) -> str: ...
