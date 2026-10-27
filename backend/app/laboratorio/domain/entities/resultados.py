from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParametroResultado:
    id: int
    codigo: str
    nombre: str
    tipo_entrada: str
    unidad: str | None
    rango_referencia: str | None
    obligatorio: bool
    orden: int
    seccion: str | None
    valor: str | None = None


@dataclass(frozen=True, slots=True)
class ResultadoEstudio:
    estudio_id: int
    referencia_estudio: str
    paciente_nombre: str
    tipo_estudio_nombre: str
    estado_estudio: str
    estado_resultado: str | None
    numero_version: int | None
    plantilla_configurada: bool
    observaciones: str | None
    parametros: tuple[ParametroResultado, ...]


@dataclass(frozen=True, slots=True)
class ValorResultadoEntrada:
    parametro_id: int
    valor: str | None


@dataclass(frozen=True, slots=True)
class BorradorResultado:
    estudio_id: int
    estado: str
    numero_version: int
