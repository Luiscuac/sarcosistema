"""Almacenamiento local de archivos: fuera de la BD, con ruta determinista."""
import asyncio
from pathlib import Path

from app.config.settings import settings


class AlmacenLocal:
    """Guarda en <dir>/{estudio_id}/{sha256}.{ext}.

    El hash vuelve el guardado idempotente: el mismo binario no se duplica.
    """

    def __init__(self, directorio: str | None = None):
        self.directorio = Path(directorio or settings.imagenes_storage_dir)

    def _carpeta_estudio(self, estudio_id: int) -> Path:
        return self.directorio / str(estudio_id)

    async def guardar(self, contenido: bytes, estudio_id: int, hash_sha256: str, extension: str) -> str:
        carpeta = self._carpeta_estudio(estudio_id)
        nombre = f'{hash_sha256}.{extension or "bin"}'
        ruta = carpeta / nombre
        await asyncio.to_thread(self._escribir, carpeta, ruta, contenido)
        return f'{estudio_id}/{nombre}'

    @staticmethod
    def _escribir(carpeta: Path, ruta: Path, contenido: bytes) -> None:
        carpeta.mkdir(parents=True, exist_ok=True)
        if not ruta.exists():
            ruta.write_bytes(contenido)

    def ruta_absoluta(self, url_archivo: str) -> str:
        raiz = self.directorio.resolve()
        ruta = (raiz / url_archivo).resolve()
        if raiz not in ruta.parents:
            raise ValueError('Ruta fuera del almacenamiento')
        if not ruta.is_file():
            raise FileNotFoundError(str(ruta))
        return str(ruta)
