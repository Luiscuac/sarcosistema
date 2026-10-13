"""
Punto de entrada de la aplicacion.
Equivalente a main.ts + app.module.ts: importa y conecta todos los modulos.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from app.config.database import engine

from app.accesos.presentation.routes.router import router as accesos_router
from app.ia.router import router as ia_router
from app.imagenes.router import router as imagenes_router
from app.laboratorio.presentation.router import router as laboratorio_router
from app.shared.exceptions import registrar_manejadores_de_error

app = FastAPI(title="Sistema Hospital Sarcobamba", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend Vite en desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores_de_error(app)

app.include_router(laboratorio_router)
app.include_router(imagenes_router)
app.include_router(accesos_router)
app.include_router(ia_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

    
@app.get("/health/db")
async def health_db():
    async with engine.connect() as conn:
        resultado = await conn.execute(
            text("select count(*) from information_schema.tables where table_schema = 'public' and table_type = 'BASE TABLE'")
        )
        return {"db": "ok", "tablas_publicas": resultado.scalar_one()}
