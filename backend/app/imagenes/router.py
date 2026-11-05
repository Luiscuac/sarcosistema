"""Composición única del módulo de imagen.

Incluye las rutas clínicas de ecografía (radiólogo), la asistencia radiológica
local con RAG (médico) y la descarga de archivos. Los routers incluidos no
llevan prefijo: lo aplica este módulo igual que `app/ia/router.py`.
"""
from fastapi import APIRouter

from app.imagenes.presentation.descargas import router as descargas_router
from app.imagenes.presentation.router_analisis import router as analisis_router
from app.imagenes.presentation.router_clinico import router as clinico_router

router = APIRouter(prefix='/imagenes', tags=['imagenes'])

router.include_router(clinico_router)
router.include_router(analisis_router)
router.include_router(descargas_router)
