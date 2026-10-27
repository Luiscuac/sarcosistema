from typing import Protocol

from app.laboratorio.domain.entities import (
    EstudioCatalogo,
    EstudioPendiente,
    ResultadoEstudio,
    TomaMuestraNueva,
    MuestraSolicitudNueva,
    ValorResultadoEntrada,
    BorradorResultado,
    PacienteNuevo,
    PacienteResumen,
    SolicitudCreada,
    SolicitudNueva,
)


class ExamenRepository(Protocol):
    async def listar_catalogo(self) -> list[EstudioCatalogo]: ...

    async def listar_pendientes(self) -> list[EstudioPendiente]: ...

    async def listar_publicados(self) -> list[EstudioPendiente]: ...

    async def buscar_pacientes(self, termino: str) -> list[PacienteResumen]: ...

    async def crear_paciente(
        self, paciente: PacienteNuevo, usuario_id: int
    ) -> PacienteResumen: ...

    async def crear_solicitud(
        self, solicitud: SolicitudNueva, usuario_id: int
    ) -> SolicitudCreada: ...

    async def recibir_muestra(
        self, toma: TomaMuestraNueva, usuario_id: int
    ) -> str: ...

    async def recibir_muestra_solicitud(
        self, toma: MuestraSolicitudNueva, usuario_id: int
    ) -> str: ...

    async def obtener_resultado(self, estudio_id: int) -> ResultadoEstudio: ...

    async def guardar_borrador(
        self,
        estudio_id: int,
        valores: tuple[ValorResultadoEntrada, ...],
        observaciones: str | None,
        usuario_id: int,
    ) -> BorradorResultado: ...

    async def publicar_resultado(self, estudio_id: int, usuario_id: int) -> BorradorResultado: ...
