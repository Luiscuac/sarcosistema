from dataclasses import dataclass


@dataclass(frozen=True)
class VentanaVisible:
    handle: int
    titulo: str
    proceso_id: int


@dataclass(frozen=True)
class CampoEditable:
    automation_id: str
    nombre: str
    tipo: str
    habilitado: bool
    selector_tipo: str
    selector: str
    indice: int
    configurable: bool


@dataclass(frozen=True)
class CampoDestino:
    selector_tipo: str
    selector: str
    valor: str


@dataclass(frozen=True)
class ConsultaParaDemo:
    paciente_nombre: str
    codigo_paciente: str
    historia_clinica: str | None
    profesional: str
    datos: dict[str, str | float | None]
