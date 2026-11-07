class RegistrarAdmision:
    def __init__(self, repositorio):
        self.repositorio = repositorio

    async def ejecutar(self, paciente_id: int, usuario_id: int, datos):
        if await self.repositorio.obtener_paciente(paciente_id) is None:
            raise LookupError('Paciente no encontrado.')
        return await self.repositorio.crear_borrador(paciente_id, usuario_id, datos)
