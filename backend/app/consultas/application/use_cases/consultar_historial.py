class ConsultarHistorial:
    def __init__(self, repo):
        self.repo = repo

    async def ejecutar(self, paciente_id: int, pagina: int, limite: int):
        if not await self.repo.obtener_paciente(paciente_id):
            return None
        return await self.repo.listar_historial(paciente_id, pagina, limite)
