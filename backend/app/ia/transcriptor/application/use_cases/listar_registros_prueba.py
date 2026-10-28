from app.ia.transcriptor.infrastructure.registro_repository import RepositorioRegistrosPrueba


class ListarRegistrosPrueba:
    def __init__(self, repositorio: RepositorioRegistrosPrueba):
        self.repositorio = repositorio

    def ejecutar(self):
        return self.repositorio.listar()

    def obtener(self, identificador: str):
        return self.repositorio.obtener(identificador)
