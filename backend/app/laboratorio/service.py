"""
Logica de negocio del modulo laboratorio (HU-N05).
Equivalente a examen.service.ts: validar campos, reglas del backlog.
"""
from fastapi import HTTPException

from app.laboratorio.models import Examen
from app.laboratorio.repository import ExamenRepository
from app.laboratorio.schemas import CrearExamenDTO


class ExamenService:
    def __init__(self, repository: ExamenRepository):
        self.repository = repository

    async def crear_examen(self, data: CrearExamenDTO) -> Examen:
        # Reglas de negocio especificas de HU-N05 van aca, no en el router.
        examen = Examen(paciente_id=data.paciente_id, tipo=data.tipo)
        return await self.repository.crear(examen)

    async def obtener_examen(self, examen_id: int) -> Examen:
        examen = await self.repository.obtener_por_id(examen_id)
        if examen is None:
            raise HTTPException(status_code=404, detail="Examen no encontrado")
        return examen
