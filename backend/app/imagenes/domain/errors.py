"""Errores de dominio del modulo de imagen (se traducen a HTTP en presentacion)."""


class ErrorImagen(Exception):
    """Base: el mensaje es seguro para mostrarse al usuario."""


class EstudioNoEncontrado(ErrorImagen):
    pass


class InformeNoEncontrado(ErrorImagen):
    pass


class ArchivoNoEncontrado(ErrorImagen):
    pass


class SolicitudInvalida(ErrorImagen):
    pass


class FormatoNoAdmitido(ErrorImagen):
    pass


class ArchivoDemasiadoGrande(ErrorImagen):
    pass


class DemasiadosArchivos(ErrorImagen):
    pass


class ArchivoVacio(ErrorImagen):
    pass


class InformeSinContenido(ErrorImagen):
    pass


class InformeYaPublicado(ErrorImagen):
    pass
