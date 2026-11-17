"""Casos de uso del personal de imágenes: bandeja, subida de imagenes/informe y publicacion."""
from app.imagenes.domain.entities import ArchivoImagen, InformeImagen
from app.imagenes.domain.ecografia import validar_datos, texto_informe
from app.imagenes.domain.errors import (
    ArchivoDemasiadoGrande,
    ArchivoVacio,
    EstudioNoEncontrado,
    FormatoNoAdmitido,
    InformeYaPublicado,
    InformeSinContenido,
    SolicitudInvalida,
)


class ListarBandeja:
    def __init__(self, repositorio):
        self.repositorio = repositorio

    async def ejecutar(self):
        return await self.repositorio.listar_bandeja()


class ObtenerEstudioImagen:
    def __init__(self, repositorio):
        self.repositorio = repositorio

    async def ejecutar(self, estudio_id: int):
        estudio = await self.repositorio.obtener_estudio(estudio_id)
        if estudio is None:
            raise EstudioNoEncontrado(f'El estudio {estudio_id} no existe')
        return estudio


class GuardarInforme:
    """Guarda (versiona) imagenes + texto del informe en estado borrador."""

    def __init__(self, repositorio, almacen, tipos_permitidos, max_bytes, max_archivos):
        self.repositorio = repositorio
        self.almacen = almacen
        self.tipos_permitidos = tuple(tipos_permitidos)
        self.max_bytes = max_bytes
        self.max_archivos = max_archivos

    async def ejecutar(self, estudio_id: int, descripcion: str | None,
                       entradas: list[dict], usuario_id: int, datos_ecografia: dict | None = None,
                       conservar_archivos: list[int] | None = None) -> tuple[InformeImagen, bool]:
        # entradas: [{'nombre': str, 'mime': str, 'contenido': bytes}]
        estudio = await self.repositorio.obtener_estudio(estudio_id)
        if estudio is None:
            raise EstudioNoEncontrado(f'El estudio {estudio_id} no existe')
        if estudio.informe is not None and estudio.informe.estado == 'publicado':
            raise InformeYaPublicado('El informe ya esta publicado; usa rectificar')

        anteriores = estudio.informe.archivos if estudio.informe else ()
        ids_validos = {a.id for a in anteriores}
        if conservar_archivos is not None and (
                any(type(i) is not int for i in conservar_archivos)
                or len(set(conservar_archivos)) != len(conservar_archivos)
                or not set(conservar_archivos) <= ids_validos):
            raise SolicitudInvalida('Solo se pueden conservar adjuntos de la versión actual de este estudio.')
        conservados = [a for a in anteriores if conservar_archivos is None or a.id in conservar_archivos]
        if len(entradas) + len(conservados) > self.max_archivos:
            raise ArchivoVacio(f'Como maximo {self.max_archivos} archivos por estudio')

        if datos_ecografia is not None:
            datos_ecografia = validar_datos(datos_ecografia, estudio.tipo_estudio_codigo)
            descripcion = texto_informe(datos_ecografia)
        elif estudio.informe and estudio.informe.datos_ecografia:
            raise SolicitudInvalida('Este informe requiere los campos de su plantilla de ecografía.')

        import hashlib

        archivos: list[dict] = [{
            'nombre_original': a.nombre_original, 'mime_type': a.mime_type,
            'tamano_bytes': a.tamano_bytes, 'hash_sha256': a.hash_sha256, 'url_archivo': a.url_archivo,
        } for a in conservados]
        # Validar el lote completo antes de escribir el primer archivo.
        for entrada in entradas:
            mime = (entrada.get('mime') or '').lower()
            if mime not in self.tipos_permitidos:
                raise FormatoNoAdmitido(f'Formato no admitido: {mime or entrada.get("nombre")}')
            contenido = entrada.get('contenido') or b''
            if not contenido:
                raise ArchivoVacio('El archivo llegó vacío')
            limite = self.max_bytes(mime) if callable(self.max_bytes) else self.max_bytes
            if len(contenido) > limite:
                raise ArchivoDemasiadoGrande(mime)
        for entrada in entradas:
            mime = (entrada.get('mime') or '').lower()
            contenido = entrada['contenido']
            hash_sha256 = hashlib.sha256(contenido).hexdigest()
            extension = self._extension(mime, entrada.get('nombre'))
            url = await self.almacen.guardar(contenido, estudio_id, hash_sha256, extension)
            archivos.append({
                'nombre_original': entrada.get('nombre') or f'archivo.{extension}',
                'mime_type': mime, 'tamano_bytes': len(contenido),
                'hash_sha256': hash_sha256, 'url_archivo': url,
            })
        texto = (descripcion or '').strip() or None
        if not texto and not archivos:
            raise InformeSinContenido('Escribe el informe o sube al menos una imagen')
        if datos_ecografia is not None:
            return await self.repositorio.guardar_informe(estudio_id, texto, archivos, usuario_id, datos_ecografia=datos_ecografia)
        return await self.repositorio.guardar_informe(estudio_id, texto, archivos, usuario_id)

    @staticmethod
    def _extension(mime: str, nombre: str | None) -> str:
        import os
        if nombre and '.' in nombre:
            return nombre.rsplit('.', 1)[-1].lower()[:12]
        return {  # noqa: E306
            'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp',
            'image/gif': 'gif', 'image/tiff': 'tif', 'application/pdf': 'pdf',
            'application/dicom': 'dcm',
        }.get(mime, 'bin')


class PublicarInforme:
    def __init__(self, repositorio):
        self.repositorio = repositorio

    async def ejecutar(self, estudio_id: int, usuario_id: int) -> InformeImagen:
        estudio = await self.repositorio.obtener_estudio(estudio_id)
        if estudio is None:
            raise EstudioNoEncontrado(f'El estudio {estudio_id} no existe')
        if estudio.informe is None:
            raise InformeSinContenido('No hay informe para publicar')
        if estudio.informe.estado == 'publicado':
            raise InformeYaPublicado('El informe ya estaba publicado')
        if estudio.informe.datos_ecografia:
            validar_datos(estudio.informe.datos_ecografia, estudio.tipo_estudio_codigo, publicar=True)
        informe: InformeImagen = await self.repositorio.publicar_informe(estudio_id, usuario_id)
        return informe
