from app.consultas.application.ports.consulta_repository import ConsultaRepository


class RegistrarConsulta:
    def __init__(self, repo: ConsultaRepository):
        self.repo = repo

    async def ejecutar(self, datos, usuario_id: int) -> tuple[dict, bool]:
        medico = await self.repo.medico_vigente(usuario_id)
        if medico is None:
            raise ValueError('Tu cuenta no tiene un médico activo con especialidad vigente.')
        return await self.repo.crear(datos, usuario_id, medico)
