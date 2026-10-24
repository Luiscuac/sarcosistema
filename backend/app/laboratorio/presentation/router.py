"""
Endpoints del modulo laboratorio.
Equivalente a examen.controller.ts: POST /examenes, GET /examenes/:id
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.accesos.presentation.dependencies.role_required import requiere_rol
from app.laboratorio.application.service import ExamenService
from app.laboratorio.domain.exceptions import ExamenNoEncontrado
from app.laboratorio.infrastructure.persistence.repository import SqlAlchemyExamenRepository
from app.laboratorio.presentation.schemas import CrearExamenDTO, ExamenOut

router = APIRouter(
    prefix="/examenes", tags=["laboratorio"],
    dependencies=[Depends(requiere_rol("laboratorio"))],
)


def get_service(db: AsyncSession = Depends(get_db)) -> ExamenService:
    return ExamenService(SqlAlchemyExamenRepository(db))


@router.post("", response_model=ExamenOut, status_code=201)
async def crear_examen(data: CrearExamenDTO, service: ExamenService = Depends(get_service)):
    examen = await service.crear_examen(data.paciente_id, data.tipo)
    return ExamenOut.model_validate(examen)


@router.get("/{examen_id}", response_model=ExamenOut)
async def obtener_examen(examen_id: int, service: ExamenService = Depends(get_service)):
    try:
        examen = await service.obtener_examen(examen_id)
    except ExamenNoEncontrado:
        raise HTTPException(status_code=404, detail="Examen no encontrado") from None
    return ExamenOut.model_validate(examen)
