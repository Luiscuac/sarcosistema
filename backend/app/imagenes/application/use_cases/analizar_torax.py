from app.imagenes.application.ports.vision import VisionTorax


class AnalizarTorax:
    def __init__(self, vision: VisionTorax):
        self.vision = vision

    def ejecutar(self, contenido: bytes, proyeccion: str, repeticiones: int = 1) -> dict:
        return self.vision.analizar(contenido, proyeccion, repeticiones)
