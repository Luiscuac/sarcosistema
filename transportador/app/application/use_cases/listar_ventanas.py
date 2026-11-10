from app.application.ports.automatizacion_escritorio import AutomatizacionEscritorio


class ListarVentanas:
    def __init__(self, escritorio: AutomatizacionEscritorio):
        self.escritorio = escritorio

    def ejecutar(self):
        return self.escritorio.listar_ventanas_visibles()
