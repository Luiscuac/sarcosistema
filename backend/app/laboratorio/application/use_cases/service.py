from dataclasses import replace
from datetime import date

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
    IncidenciaNueva,
    IncidenciaSolicitudNueva,
    ValorResultadoEntrada,
)


class LaboratorioService:
    """Casos de uso del módulo de laboratorio."""

    def __init__(self, repository: ExamenRepository):
        self.repository = repository

    async def listar_solicitudes_paciente(self, paciente_id: int, usuario_id: int):
        return await self.repository.listar_solicitudes_paciente(paciente_id, usuario_id)

    async def listar_medicos(self, termino: str):
        return await self.repository.listar_medicos(termino.strip())

    async def obtener_informe_medico(self, solicitud_id: int, usuario_id: int):
        if await self.repository.obtener_solicitud_medico(solicitud_id, usuario_id) is None:
            return None
        return await self.obtener_informe(solicitud_id)

    async def obtener_solicitud(self, solicitud_id: int):
        return await self.repository.obtener_solicitud(solicitud_id)

    async def obtener_informe(self, solicitud_id: int):
        solicitud = await self.repository.obtener_solicitud(solicitud_id)
        if solicitud is None:
            return None
        estudios = solicitud["estudios"]
        estados_finales = {"publicado", "no_realizado"}
        if not estudios or any(estudio["estado"] not in estados_finales for estudio in estudios):
            raise ValueError(
                "El informe final estará disponible cuando todos los estudios estén publicados o cerrados como no realizados"
            )

        resultados = []
        no_realizados = []
        for estudio in estudios:
            if estudio["estado"] == "no_realizado":
                incidencia = estudio["incidencias"][-1] if estudio["incidencias"] else None
                no_realizados.append({
                    "nombre": estudio["tipo_estudio_nombre"],
                    "categoria": estudio["categoria_laboratorio"],
                    "referencia": estudio["referencia_estudio"],
                    "motivo": incidencia["motivo"] if incidencia else "toma_no_realizada",
                    "descripcion": incidencia["descripcion"] if incidencia else "Sin detalle registrado",
                    "responsable": incidencia["responsable"] if incidencia else "No registrado",
                    "fecha_hora": incidencia["fecha_hora"] if incidencia else solicitud["fecha_registro"],
                })
                continue
            resultado = await self.repository.obtener_resultado(estudio["estudio_id"])
            if resultado.estado_resultado != "publicado":
                raise ValueError("El informe final estará disponible cuando todos los resultados estén publicados")
            parametros = [
                {
                    "nombre": parametro.nombre,
                    "seccion": parametro.seccion,
                    "valor": parametro.valor.strip(),
                    "unidad": parametro.unidad,
                    "rango_referencia": parametro.rango_referencia,
                }
                for parametro in resultado.parametros
                if parametro.codigo != "unidad_reportada" and parametro.valor is not None and parametro.valor.strip()
            ]
            resultados.append({
                "nombre": resultado.tipo_estudio_nombre,
                "categoria": estudio["categoria_laboratorio"],
                "referencia": resultado.referencia_estudio,
                "parametros": parametros,
                "observaciones": resultado.observaciones.strip() if resultado.observaciones else None,
                "responsable_publicacion": resultado.responsable_publicacion,
            })
        return {
            "referencia": solicitud["referencia"],
            "paciente_nombre": solicitud["paciente_nombre"],
            "paciente_documento": solicitud["paciente_documento"],
            "fecha_solicitud": solicitud["fecha_solicitud"],
            "referencia_papel_formulario": solicitud["referencia_papel_formulario"],
            "procedencia": solicitud["procedencia"],
            "establecimiento_solicitante_nombre": solicitud["establecimiento_solicitante_nombre"],
            "medico_solicitante_nombre": solicitud["medico_solicitante_nombre"],
            "resultados": resultados,
            "estudios_no_realizados": no_realizados,
        }

    async def listar_catalogo(self) -> list[EstudioCatalogo]:
        return await self.repository.listar_catalogo()

    async def listar_pendientes(self) -> list[EstudioPendiente]:
        return await self.repository.listar_pendientes()

    async def listar_publicados(self) -> list[EstudioPendiente]:
        return await self.repository.listar_publicados()

    async def buscar_pacientes(self, termino: str) -> list[PacienteResumen]:
        termino = termino.strip()
        if not termino:
            return []
        return await self.repository.buscar_pacientes(termino)

    async def crear_paciente(
        self, paciente: PacienteNuevo, usuario_id: int
    ) -> PacienteResumen:
        if paciente.fecha_nacimiento > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        paciente = replace(
            paciente,
            tipo_documento=(paciente.tipo_documento or "").strip() or None,
            numero_documento=(paciente.numero_documento or "").strip() or None,
        )
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
                telefono=paciente.telefono,
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
        if solicitud.procedencia == "otro_centro" and not (solicitud.establecimiento_solicitante_nombre or "").strip():
            raise ValueError("Indica el nombre del otro centro")
        if solicitud.procedencia == "este_centro" and solicitud.medico_solicitante_id is None:
            raise ValueError("Selecciona un médico registrado de Sarcobamba")
        if solicitud.procedencia == "otro_centro" and solicitud.medico_solicitante_id is not None:
            raise ValueError("El médico de otro centro se registra por nombre")
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

    async def registrar_incidencia(self, incidencia: IncidenciaNueva, usuario_id: int):
        return await self.repository.registrar_incidencia(incidencia, usuario_id)

    async def registrar_incidencias_solicitud(self, incidencia: IncidenciaSolicitudNueva, usuario_id: int) -> int:
        if not incidencia.estudio_ids or len(incidencia.estudio_ids) != len(set(incidencia.estudio_ids)):
            raise ValueError("Selecciona estudios distintos para la incidencia")
        return await self.repository.registrar_incidencias_solicitud(incidencia, usuario_id)

    async def obtener_resultado(self, estudio_id: int):
        return await self.repository.obtener_resultado(estudio_id)

    async def guardar_borrador(
        self, estudio_id: int, valores: tuple[ValorResultadoEntrada, ...],
        observaciones: str | None, usuario_id: int, responsable_analisis: str,
    ):
        return await self.repository.guardar_borrador(
            estudio_id, valores, observaciones, usuario_id, responsable_analisis
        )

    async def guardar_borrador_area(
        self, solicitud_id: int, area_codigo: str, estudios, observaciones: str | None,
        usuario_id: int, responsable: str,
    ):
        solicitud = await self.repository.obtener_solicitud(solicitud_id)
        if solicitud is None:
            raise ValueError("La solicitud no existe")
        disponibles = {
            item["estudio_id"] for item in solicitud["estudios"]
            if item["categoria_laboratorio"] == area_codigo and item["estado"] != "pendiente_muestra"
        }
        ids = [item[0] for item in estudios]
        if not ids or len(ids) != len(set(ids)) or not set(ids).issubset(disponibles):
            raise ValueError("Los estudios no pertenecen al área de esta solicitud")
        resultados = []
        for estudio_id, valores in estudios:
            resultados.append(await self.repository.guardar_borrador(
                estudio_id, valores, observaciones, usuario_id, responsable,
            ))
        return resultados

    async def publicar_resultados_area(
        self, solicitud_id: int, area_codigo: str, estudio_ids: tuple[int, ...], usuario_id: int,
        responsable: str,
    ):
        solicitud = await self.repository.obtener_solicitud(solicitud_id)
        if solicitud is None:
            raise ValueError("La solicitud no existe")
        disponibles = {
            item["estudio_id"] for item in solicitud["estudios"]
            if item["categoria_laboratorio"] == area_codigo
            and item["estado"] != "pendiente_muestra"
            and item["estado"] != "publicado"
        }
        if not estudio_ids or len(estudio_ids) != len(set(estudio_ids)) or not set(estudio_ids).issubset(disponibles):
            raise ValueError("Los estudios no pendientes pertenecen al área de esta solicitud")
        resultados = []
        for estudio_id in estudio_ids:
            resultados.append(await self.repository.publicar_resultado(estudio_id, usuario_id, responsable))
        return resultados

    async def publicar_resultado(self, estudio_id: int, usuario_id: int, responsable_publicacion: str):
        return await self.repository.publicar_resultado(estudio_id, usuario_id, responsable_publicacion)
