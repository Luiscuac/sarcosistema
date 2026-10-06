"""
Manejo uniforme de errores (patron "informar el error").
Equivalente a error.interceptor.ts
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def registrar_manejadores_de_error(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def manejador_generico(request: Request, exc: Exception):
        # TODO: loguear con sentry-sdk / structlog antes de responder
        return JSONResponse(
            status_code=500,
            content={"detalle": "Ocurrio un error interno inesperado."},
        )
