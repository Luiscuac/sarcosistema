"""
Endpoints del modulo laboratorio.
Equivalente a examen.controller.ts: POST /examenes, GET /examenes/:id
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.laboratorio.repository import ExamenRepository
from app.laboratorio.schemas import CrearExamenDTO, ExamenOut
from app.laboratorio.service import ExamenService

router = APIRouter(prefix="/examenes", tags=["laboratorio"])


def get_service(db: AsyncSession = Depends(get_db)) -> ExamenService:
    return ExamenService(ExamenRepository(db))


@router.post("", response_model=ExamenOut, status_code=201)
async def crear_examen(data: CrearExamenDTO, service: ExamenService = Depends(get_service)):
    return await service.crear_examen(data)


@router.get("/{examen_id}", response_model=ExamenOut)
async def obtener_examen(examen_id: int, service: ExamenService = Depends(get_service)):
    return await service.obtener_examen(examen_id)
