from app.application.ports.automatizacion_escritorio import AutomatizacionEscritorio
from app.domain.entities import CampoDestino


class RellenarCampos:
    def __init__(self, escritorio: AutomatizacionEscritorio):
        self.escritorio = escritorio

    def ejecutar(self, handle: int, campos: list[CampoDestino]):
        self.escritorio.obtener_ventana_visible(handle)
        completados = self.escritorio.rellenar_campos(handle, campos)
        return {
            "estado": "campos_rellenados",
            "campos": completados,
            "guardar_automaticamente": False,
            "mensaje": "Campos rellenados. Revisa los valores antes de guardarlos en la aplicación destino.",
        }
