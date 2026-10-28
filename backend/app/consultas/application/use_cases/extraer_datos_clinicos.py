from uuid import uuid4


class ExtraerDatosClinicos:
    def __init__(self, repo, extractor):
        self.repo = repo
        self.extractor = extractor

    async def ejecutar(self, paciente_id: int, transcripcion: str):
        if await self.repo.obtener_paciente(paciente_id) is None:
            raise LookupError('Paciente no encontrado.')
        propuesta = await self.extractor.extraer(transcripcion)
        return {
            'campos_extraidos': propuesta.campos, 'advertencias': propuesta.advertencias,
            'bloqueada': propuesta.bloqueada, 'requiere_revision': True,
            'propuesta_id': uuid4(), 'modelo': self.extractor.modelo,
        }
