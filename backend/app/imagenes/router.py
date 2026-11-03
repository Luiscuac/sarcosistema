"""Endpoints del modulo imagenes (Grupo B del backlog)."""
from fastapi import APIRouter
from app.imagenes.presentation.router import router as clinico_router

router = APIRouter(prefix="/imagenes", tags=["imagenes"])

router.include_router(clinico_router)
