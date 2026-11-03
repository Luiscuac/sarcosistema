class ErrorTransportador(Exception):
    """Error conocido del agente de automatización local."""

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class VentanaNoEncontrada(ErrorTransportador):
    pass


class VentanaAmbigua(ErrorTransportador):
    pass


class ControlNoEncontrado(ErrorTransportador):
    pass


class SelectorAmbiguo(ErrorTransportador):
    pass


class ControlDeshabilitado(ErrorTransportador):
    pass


class ContenidoInvalido(ErrorTransportador):
    pass


class FalloUIA(ErrorTransportador):
    pass
