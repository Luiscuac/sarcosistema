from app.consultas.domain.validators import buscar_normalizado


class ConsultarPacientes:
    def __init__(self, repo):
        self.repo = repo

    async def ejecutar(self, buscar: str, pagina: int, limite: int):
        return await self.repo.buscar_pacientes(buscar_normalizado(buscar), pagina, limite)
