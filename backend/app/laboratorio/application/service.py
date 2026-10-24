from app.laboratorio.application.ports.examen_repository import ExamenRepository
from app.laboratorio.domain.entities import Examen
from app.laboratorio.domain.exceptions import ExamenNoEncontrado


class ExamenService:
    """Casos de uso de laboratorio, independientes de HTTP y SQLAlchemy."""

    def __init__(self, repository: ExamenRepository):
        self.repository = repository

    async def crear_examen(self, paciente_id: int, tipo: str) -> Examen:
        examen = Examen(id=None, paciente_id=paciente_id, tipo=tipo.strip())
        return await self.repository.crear(examen)

    async def obtener_examen(self, examen_id: int) -> Examen:
        examen = await self.repository.obtener_por_id(examen_id)
        if examen is None:
            raise ExamenNoEncontrado(examen_id)
        return examen
