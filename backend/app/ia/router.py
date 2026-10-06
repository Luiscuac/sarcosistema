"""Endpoints del componente de IA (dictado de informes/recetas)."""
from fastapi import APIRouter

router = APIRouter(prefix="/ia", tags=["ia"])

# TODO: endpoint de transcripcion; la IA propone, el profesional valida y confirma
