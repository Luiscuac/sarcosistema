import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.presentation.exception_handlers import registrar_manejadores
from app.presentation.routes.router import router


FRONTEND_ORIGINS = {
    origin.strip()
    for origin in os.getenv(
        "TRANSPORTADOR_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
}

app = FastAPI(
    title="Agente local SarcoSistema",
    version="0.1.0",
    description="Agente local UIA para transportar consultas al cuaderno de demostración de Windows.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(FRONTEND_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
registrar_manejadores(app)
app.include_router(router)


@app.middleware("http")
async def rechazar_origenes_web_desconocidos(request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in FRONTEND_ORIGINS:
        return JSONResponse(status_code=403, content={"detail": "Origen web no permitido."})
    return await call_next(request)
