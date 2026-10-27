from app.laboratorio.application.ports.examen_repository import ExamenRepository
from app.laboratorio.domain.entities import (
    EstudioCatalogo,
    EstudioPendiente,
    PacienteNuevo,
    PacienteResumen,
    SolicitudCreada,
    SolicitudNueva,
    TomaMuestraNueva,
    MuestraSolicitudNueva,
    ValorResultadoEntrada,
)


class LaboratorioService:
    """Casos de uso del módulo de laboratorio."""

    def __init__(self, repository: ExamenRepository):
        self.repository = repository

    async def listar_catalogo(self) -> list[EstudioCatalogo]:
        return await self.repository.listar_catalogo()

    async def listar_pendientes(self) -> list[EstudioPendiente]:
        return await self.repository.listar_pendientes()

    async def listar_publicados(self) -> list[EstudioPendiente]:
        return await self.repository.listar_publicados()

    async def buscar_pacientes(self, termino: str) -> list[PacienteResumen]:
        return await self.repository.buscar_pacientes(termino.strip())

    async def crear_paciente(
        self, paciente: PacienteNuevo, usuario_id: int
    ) -> PacienteResumen:
        if paciente.sin_documento:
            paciente = PacienteNuevo(
                nombre_completo=paciente.nombre_completo.strip(),
                fecha_nacimiento=paciente.fecha_nacimiento,
                sexo=paciente.sexo,
                tipo_documento=None,
                numero_documento=None,
                sin_documento=True,
                historia_clinica=paciente.historia_clinica,
                codigo_externo=paciente.codigo_externo,
            )
        elif not paciente.tipo_documento or not paciente.numero_documento:
            raise ValueError("Se requiere documento o marcar que la persona no tiene documento")
        return await self.repository.crear_paciente(paciente, usuario_id)

    async def crear_solicitud(
        self, solicitud: SolicitudNueva, usuario_id: int
    ) -> SolicitudCreada:
        ids = solicitud.tipo_estudio_ids
        if not ids:
            raise ValueError("Selecciona al menos un estudio")
        if len(ids) != len(set(ids)):
            raise ValueError("No repitas el mismo estudio en una solicitud")
        if not solicitud.medico_solicitante_nombre.strip():
            raise ValueError("Registra el nombre del profesional solicitante")
        return await self.repository.crear_solicitud(solicitud, usuario_id)

    async def recibir_muestra(self, toma: TomaMuestraNueva, usuario_id: int) -> str:
        if not toma.tipo_muestra.strip():
            raise ValueError("Indica el tipo de muestra recibido")
        if toma.hora_no_registrada and toma.hora_toma is not None:
            raise ValueError("Si la hora no se registró, deja la hora vacía")
        if not toma.hora_no_registrada and toma.hora_toma is None:
            raise ValueError("Registra la hora o marca que no fue registrada")
        return await self.repository.recibir_muestra(toma, usuario_id)

    async def recibir_muestra_solicitud(
        self, toma: MuestraSolicitudNueva, usuario_id: int
    ) -> str:
        if not toma.estudio_ids or len(toma.estudio_ids) != len(set(toma.estudio_ids)):
            raise ValueError("Selecciona estudios distintos para esta muestra")
        if not toma.tipo_muestra.strip():
            raise ValueError("Indica el tipo de muestra recibido")
        if toma.hora_no_registrada == (toma.hora_toma is not None):
            raise ValueError("Registra una hora o marca que no fue registrada")
        return await self.repository.recibir_muestra_solicitud(toma, usuario_id)

    async def obtener_resultado(self, estudio_id: int):
        return await self.repository.obtener_resultado(estudio_id)

    async def guardar_borrador(
        self, estudio_id: int, valores: tuple[ValorResultadoEntrada, ...],
        observaciones: str | None, usuario_id: int,
    ):
        return await self.repository.guardar_borrador(
            estudio_id, valores, observaciones, usuario_id
        )

    async def publicar_resultado(self, estudio_id: int, usuario_id: int):
        return await self.repository.publicar_resultado(estudio_id, usuario_id)
