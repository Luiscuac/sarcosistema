from typing import Protocol, TypedDict


class PropuestaEcografia(TypedDict):
    campo: str
    organo: str | None
    valor: str
    evidencia: str
    ambiguo: bool
    alertas: list[str]


class ResultadoExtraccionEcografia(TypedDict):
    campos_extraidos: list[PropuestaEcografia]
    advertencias: list[str]
    bloqueada: bool


class ExtractorEcografia(Protocol):
    modelo: str

    async def extraer(
        self, transcripcion: str, organos: tuple[str, ...]
    ) -> ResultadoExtraccionEcografia: ...
