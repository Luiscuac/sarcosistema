"""Adjuntos privados en un depósito compatible con S3."""

import asyncio
from functools import lru_cache

from app.config.settings import settings


class AlmacenNoDisponible(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _cliente():
    import boto3
    from botocore.config import Config

    if not (
        settings.imagenes_s3_endpoint
        and settings.imagenes_s3_endpoint.startswith("https://")
        and settings.imagenes_s3_access_key
        and settings.imagenes_s3_secret_key
    ):
        raise AlmacenNoDisponible("El almacenamiento privado no está configurado.")
    return boto3.client(
        "s3",
        endpoint_url=settings.imagenes_s3_endpoint,
        region_name=settings.imagenes_s3_region,
        aws_access_key_id=settings.imagenes_s3_access_key,
        aws_secret_access_key=settings.imagenes_s3_secret_key,
        config=Config(
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            connect_timeout=5,
            read_timeout=20,
        ),
    )


class AlmacenS3:
    async def guardar(self, contenido: bytes, estudio_id: int, hash_sha256: str, extension: str) -> str:
        from botocore.exceptions import BotoCoreError, ClientError

        clave = f"{estudio_id}/{hash_sha256}.{extension or 'bin'}"
        try:
            await asyncio.to_thread(
                lambda: _cliente().put_object(Bucket=settings.imagenes_s3_bucket, Key=clave, Body=contenido),
            )
        except (BotoCoreError, ClientError) as error:
            raise AlmacenNoDisponible("No se pudo guardar el adjunto.") from error
        return clave

    async def leer(self, clave: str, tamano: int) -> bytes:
        return await asyncio.to_thread(self._leer, clave, tamano)

    @staticmethod
    def _leer(clave: str, tamano: int) -> bytes:
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            objeto = _cliente().get_object(Bucket=settings.imagenes_s3_bucket, Key=clave)
            cuerpo = objeto["Body"]
            try:
                if objeto.get("ContentLength") != tamano:
                    raise AlmacenNoDisponible("El tamaño del adjunto no coincide.")
                return cuerpo.read()
            finally:
                cuerpo.close()
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in {"NoSuchKey", "404", "NotFound"}:
                raise FileNotFoundError(clave) from None
            raise AlmacenNoDisponible("No se pudo recuperar el adjunto.") from error
        except BotoCoreError as error:
            raise AlmacenNoDisponible("No se pudo recuperar el adjunto.") from error
