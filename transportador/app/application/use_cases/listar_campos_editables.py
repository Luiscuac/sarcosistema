from app.application.ports.automatizacion_escritorio import AutomatizacionEscritorio


class ListarCamposEditables:
    def __init__(self, escritorio: AutomatizacionEscritorio):
        self.escritorio = escritorio

    def ejecutar(self, handle: int):
        self.escritorio.obtener_ventana_visible(handle)
        return self.escritorio.listar_campos_editables(handle)
