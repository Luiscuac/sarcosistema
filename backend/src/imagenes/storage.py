"""
Sube/recupera archivos del almacenamiento externo (no de la BD).
Equivalente a imagen-storage.service.ts
"""


class ImagenStorageService:
    async def subir(self, archivo_bytes: bytes, nombre: str) -> str:
        """Devuelve la URL/ruta donde quedo guardado el archivo."""
        raise NotImplementedError

    async def obtener_url(self, referencia: str) -> str:
        raise NotImplementedError
