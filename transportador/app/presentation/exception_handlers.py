from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.errors import (
    ContenidoInvalido,
    ControlDeshabilitado,
    ControlNoEncontrado,
    ErrorTransportador,
    FalloUIA,
    SelectorAmbiguo,
    VentanaAmbigua,
    VentanaNoEncontrada,
)


CODIGOS_HTTP = {
    VentanaNoEncontrada: 404,
    ControlNoEncontrado: 404,
    VentanaAmbigua: 409,
    SelectorAmbiguo: 409,
    ControlDeshabilitado: 409,
    ContenidoInvalido: 422,
    FalloUIA: 503,
}


def registrar_manejadores(app: FastAPI):
    @app.exception_handler(ErrorTransportador)
    async def manejar_error_transportador(_request: Request, error: ErrorTransportador):
        return JSONResponse(
            status_code=CODIGOS_HTTP.get(type(error), 422),
            content={"detail": error.detail},
        )
