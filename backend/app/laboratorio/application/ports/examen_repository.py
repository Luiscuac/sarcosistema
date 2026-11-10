from typing import Protocol

from app.laboratorio.domain.entities import (
    EstudioCatalogo,
    EstudioPendiente,
    ResultadoEstudio,
    TomaMuestraNueva,
    MuestraSolicitudNueva,
    IncidenciaNueva,
    IncidenciaSolicitudNueva,
    ValorResultadoEntrada,
    BorradorResultado,
    PacienteNuevo,
    PacienteResumen,
    SolicitudCreada,
    SolicitudNueva,
)


class ExamenRepository(Protocol):
    async def listar_solicitudes_paciente(self, paciente_id: int, usuario_id: int): ...
    async def listar_medicos(self, termino: str): ...
    async def obtener_solicitud_medico(self, solicitud_id: int, usuario_id: int): ...
    async def obtener_resultado_medico(self, estudio_id: int, usuario_id: int) -> ResultadoEstudio | None: ...
    async def registrar_incidencia(self, incidencia: IncidenciaNueva, usuario_id: int): ...
    async def registrar_incidencias_solicitud(self, incidencia: IncidenciaSolicitudNueva, usuario_id: int) -> int: ...
    async def obtener_solicitud(self, solicitud_id: int): ...
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
        responsable_analisis: str,
    ) -> BorradorResultado: ...

    async def publicar_resultado(self, estudio_id: int, usuario_id: int, responsable_publicacion: str) -> BorradorResultado: ...
