from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from sqlalchemy import case, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.laboratorio.domain.entities import (
    EstudioCatalogo,
    EstudioPendiente,
    EstudioSolicitadoResumen,
    AccionAuditoria,
    ParametroResultado,
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
from app.laboratorio.infrastructure.persistence.models import (
    AuditoriaAccion,
    EstudioSolicitado,
    Muestra,
    MuestraEstudio,
    ParametroPlantilla,
    ResultadoLaboratorio,
    SeccionPlantilla,
    DetalleValorResultado,
    VersionResultado,
    PlantillaExamenVersion,
    Servicio,
    Solicitud,
    TipoEstudio,
)
from app.shared.entities.paciente import Paciente


def campos_obligatorios_faltantes(parametros, detalles) -> list[str]:
    """Un registro de detalle vacío no equivale a un resultado informado."""
    informados = {
        detalle.parametro_id
        for detalle in detalles
        if any(
            valor is not None and (not isinstance(valor, str) or bool(valor.strip()))
            for valor in (
                detalle.valor_entero,
                detalle.valor_decimal,
                detalle.valor_texto,
                detalle.valor_cualitativo,
            )
        )
    }
    return [p.nombre for p in parametros if p.obligatorio and p.id not in informados]


class SqlAlchemyExamenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar_catalogo(self) -> list[EstudioCatalogo]:
        version_activa = exists(
            select(PlantillaExamenVersion.id).where(
                PlantillaExamenVersion.plantilla_examen_id
                == TipoEstudio.plantilla_examen_id,
                PlantillaExamenVersion.estado == "activa",
            )
        )
        statement = (
            select(
                TipoEstudio.id,
                TipoEstudio.codigo,
                TipoEstudio.nombre,
                TipoEstudio.requiere_muestra,
                TipoEstudio.requiere_informe,
                version_activa.label("plantilla_configurada"),
                TipoEstudio.categoria_laboratorio,
            )
            .join(Servicio, Servicio.id == TipoEstudio.servicio_id)
            .where(
                TipoEstudio.activo.is_(True),
                Servicio.activo.is_(True),
                Servicio.codigo == "LAB",
            )
            .order_by(TipoEstudio.nombre, TipoEstudio.codigo)
        )
        rows = (await self.db.execute(statement)).mappings().all()
        return [EstudioCatalogo(**row) for row in rows]

    async def listar_pendientes(self) -> list[EstudioPendiente]:
        return await self._listar_estudios(("pendiente_muestra", "resultado_en_preparacion"))

    async def listar_publicados(self) -> list[EstudioPendiente]:
        return await self._listar_estudios(("publicado",))

    async def _listar_estudios(self, estados: tuple[str, ...]) -> list[EstudioPendiente]:
        prioridad_orden = case((Solicitud.prioridad == "urgente", 0), else_=1)
        statement = (
            select(
                EstudioSolicitado.id.label("estudio_id"),
                EstudioSolicitado.referencia.label("referencia_estudio"),
                Solicitud.id.label("solicitud_id"),
                Solicitud.referencia.label("referencia_solicitud"),
                EstudioSolicitado.paciente_id.label("paciente_id"),
                Paciente.nombre_completo.label("paciente_nombre"),
                TipoEstudio.id.label("tipo_estudio_id"),
                TipoEstudio.nombre.label("tipo_estudio_nombre"),
                TipoEstudio.categoria_laboratorio,
                Solicitud.prioridad,
                EstudioSolicitado.estado,
                Solicitud.fecha_solicitud,
                exists(
                    select(PlantillaExamenVersion.id).where(
                        PlantillaExamenVersion.plantilla_examen_id == TipoEstudio.plantilla_examen_id,
                        PlantillaExamenVersion.estado == "activa",
                    )
                ).label("plantilla_configurada"),
            )
            .join(Solicitud, Solicitud.id == EstudioSolicitado.solicitud_id)
            .join(Paciente, Paciente.id == EstudioSolicitado.paciente_id)
            .join(TipoEstudio, TipoEstudio.id == EstudioSolicitado.tipo_estudio_id)
            .join(Servicio, Servicio.id == EstudioSolicitado.servicio_id)
            .where(
                EstudioSolicitado.estado.in_(estados),
                TipoEstudio.activo.is_(True),
                Servicio.codigo == "LAB",
            )
            .order_by(prioridad_orden, Solicitud.fecha_solicitud, Solicitud.id)
        )
        rows = (await self.db.execute(statement)).mappings().all()
        return [EstudioPendiente(**row) for row in rows]

    async def buscar_pacientes(self, termino: str) -> list[PacienteResumen]:
        patron = f"%{termino}%"
        statement = (
            select(
                Paciente.id,
                Paciente.codigo_paciente,
                Paciente.nombre_completo,
                Paciente.numero_documento,
                Paciente.fecha_nacimiento,
                Paciente.sexo,
                Paciente.historia_clinica,
                Paciente.codigo_externo,
            )
            .where(
                Paciente.estado == "activo",
                or_(
                    Paciente.nombre_completo.ilike(patron),
                    Paciente.numero_documento.ilike(patron),
                    Paciente.codigo_paciente.ilike(patron),
                    Paciente.historia_clinica.ilike(patron),
                    Paciente.codigo_externo.ilike(patron),
                ),
            )
            .order_by(Paciente.nombre_completo, Paciente.id)
            .limit(30)
        )
        rows = (await self.db.execute(statement)).mappings().all()
        return [PacienteResumen(**row) for row in rows]

    async def crear_paciente(
        self, paciente: PacienteNuevo, usuario_id: int
    ) -> PacienteResumen:
        modelo = Paciente(
            codigo_paciente=f"PAC-{uuid4().hex[:12].upper()}",
            tipo_documento=paciente.tipo_documento,
            numero_documento=paciente.numero_documento,
            sin_documento=paciente.sin_documento,
            historia_clinica=paciente.historia_clinica,
            codigo_externo=paciente.codigo_externo,
            nombre_completo=paciente.nombre_completo,
            fecha_nacimiento=paciente.fecha_nacimiento,
            sexo=paciente.sexo,
            estado="activo",
        )
        self.db.add(modelo)
        await self.db.flush()
        self.db.add(
            AuditoriaAccion(
                fecha_hora=datetime.now(timezone.utc),
                usuario_id=usuario_id,
                accion=AccionAuditoria.CREAR,
                entidad_afectada="paciente",
                referencia_registro=str(modelo.id),
                detalle={"codigo_paciente": modelo.codigo_paciente},
            )
        )
        await self.db.flush()
        return PacienteResumen(
            id=modelo.id,
            codigo_paciente=modelo.codigo_paciente,
            nombre_completo=modelo.nombre_completo,
            numero_documento=modelo.numero_documento,
            fecha_nacimiento=modelo.fecha_nacimiento,
            sexo=modelo.sexo,
            historia_clinica=modelo.historia_clinica,
            codigo_externo=modelo.codigo_externo,
        )

    async def crear_solicitud(
        self, solicitud: SolicitudNueva, usuario_id: int
    ) -> SolicitudCreada:
        existente = (
            await self.db.execute(
                select(Solicitud).where(
                    Solicitud.clave_idempotencia == solicitud.clave_idempotencia
                )
            )
        ).scalar_one_or_none()
        if existente is not None:
            filas = (
                await self.db.execute(
                    select(EstudioSolicitado, TipoEstudio.nombre)
                    .join(TipoEstudio, TipoEstudio.id == EstudioSolicitado.tipo_estudio_id)
                    .where(EstudioSolicitado.solicitud_id == existente.id)
                    .order_by(EstudioSolicitado.id)
                )
            ).all()
            ids_existentes = tuple(sorted(fila[0].tipo_estudio_id for fila in filas))
            if (
                existente.paciente_id != solicitud.paciente_id
                or ids_existentes != tuple(sorted(solicitud.tipo_estudio_ids))
            ):
                raise ValueError("La clave de envío ya se usó con otros datos")
            paciente = await self.db.get(Paciente, existente.paciente_id)
            return SolicitudCreada(
                id=existente.id,
                referencia=existente.referencia,
                paciente_id=existente.paciente_id,
                paciente_nombre=paciente.nombre_completo,
                fecha_solicitud=existente.fecha_solicitud,
                prioridad=existente.prioridad,
                estudios=tuple(
                    EstudioSolicitadoResumen(
                        id=fila[0].id,
                        referencia=fila[0].referencia,
                        tipo_estudio_id=fila[0].tipo_estudio_id,
                        tipo_estudio_nombre=fila[1],
                        estado=fila[0].estado,
                    )
                    for fila in filas
                ),
            )

        paciente = await self.db.get(Paciente, solicitud.paciente_id)
        if paciente is None or paciente.estado != "activo":
            raise ValueError("El paciente no existe o está inactivo")

        tipos = (
            await self.db.execute(
                select(TipoEstudio.id, TipoEstudio.nombre, TipoEstudio.servicio_id)
                .join(Servicio, Servicio.id == TipoEstudio.servicio_id)
                .where(
                    TipoEstudio.id.in_(solicitud.tipo_estudio_ids),
                    TipoEstudio.activo.is_(True),
                    Servicio.activo.is_(True),
                    Servicio.codigo == "LAB",
                )
            )
        ).all()
        if len(tipos) != len(solicitud.tipo_estudio_ids):
            raise ValueError("Uno o más estudios no están disponibles en el catálogo del laboratorio")
        tipos_por_id = {tipo.id: tipo for tipo in tipos}

        referencia = f"SOL-{solicitud.fecha_solicitud:%y%m%d}-{uuid4().hex[:6].upper()}"
        modelo = Solicitud(
            referencia=referencia,
            paciente_id=solicitud.paciente_id,
            referencia_papel_formulario=solicitud.referencia_papel_formulario,
            fecha_solicitud=solicitud.fecha_solicitud,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            establecimiento_solicitante_nombre_snapshot=solicitud.establecimiento_solicitante_nombre,
            medico_solicitante_nombre_snapshot=solicitud.medico_solicitante_nombre.strip(),
            diagnostico_principal=solicitud.diagnostico_principal,
            prioridad=solicitud.prioridad,
            clave_idempotencia=solicitud.clave_idempotencia,
            created_by=usuario_id,
            updated_by=usuario_id,
        )
        self.db.add(modelo)
        await self.db.flush()

        estudios_creados = []
        for tipo_id in solicitud.tipo_estudio_ids:
            tipo = tipos_por_id[tipo_id]
            estudio = EstudioSolicitado(
                referencia=f"EST-{uuid4().hex[:10].upper()}",
                solicitud_id=modelo.id,
                paciente_id=solicitud.paciente_id,
                servicio_id=tipo.servicio_id,
                tipo_estudio_id=tipo.id,
                estado="pendiente_muestra",
                created_by=usuario_id,
                updated_by=usuario_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(estudio)
            await self.db.flush()
            estudios_creados.append(
                EstudioSolicitadoResumen(
                    id=estudio.id,
                    referencia=estudio.referencia,
                    tipo_estudio_id=tipo.id,
                    tipo_estudio_nombre=tipo.nombre,
                    estado=estudio.estado,
                )
            )

        self.db.add(
            AuditoriaAccion(
                fecha_hora=datetime.now(timezone.utc),
                usuario_id=usuario_id,
                accion=AccionAuditoria.CREAR,
                entidad_afectada="solicitud",
                referencia_registro=referencia,
                detalle={
                    "cantidad_estudios": len(estudios_creados),
                    "prioridad": solicitud.prioridad,
                },
            )
        )
        await self.db.flush()
        return SolicitudCreada(
            id=modelo.id,
            referencia=modelo.referencia,
            paciente_id=paciente.id,
            paciente_nombre=paciente.nombre_completo,
            fecha_solicitud=modelo.fecha_solicitud,
            prioridad=modelo.prioridad,
            estudios=tuple(estudios_creados),
        )

    async def recibir_muestra(self, toma: TomaMuestraNueva, usuario_id: int) -> str:
        solicitud_id = (await self.db.execute(
            select(EstudioSolicitado.solicitud_id)
            .where(EstudioSolicitado.id == toma.estudio_id)
        )).scalar_one_or_none()
        if solicitud_id is None:
            raise ValueError("El estudio no existe")
        return await self.recibir_muestra_solicitud(
            MuestraSolicitudNueva(
                solicitud_id=solicitud_id,
                estudio_ids=(toma.estudio_id,),
                tipo_muestra=toma.tipo_muestra,
                fecha_toma=toma.fecha_toma,
                hora_toma=toma.hora_toma,
                hora_no_registrada=toma.hora_no_registrada,
            ),
            usuario_id,
        )

    async def recibir_muestra_solicitud(
        self, toma: MuestraSolicitudNueva, usuario_id: int
    ) -> str:
        if not toma.estudio_ids or len(toma.estudio_ids) != len(set(toma.estudio_ids)):
            raise ValueError("Selecciona estudios distintos para esta muestra")
        solicitud = (await self.db.execute(
            select(Solicitud)
            .where(Solicitud.id == toma.solicitud_id)
            .with_for_update()
        )).scalar_one_or_none()
        if solicitud is None:
            raise ValueError("La solicitud no existe")
        estudios = (await self.db.execute(
            select(EstudioSolicitado)
            .join(Servicio, Servicio.id == EstudioSolicitado.servicio_id)
            .where(
                EstudioSolicitado.id.in_(toma.estudio_ids),
                EstudioSolicitado.solicitud_id == toma.solicitud_id,
                Servicio.codigo == "LAB",
            )
            .order_by(EstudioSolicitado.id)
            .with_for_update(of=EstudioSolicitado)
        )).scalars().all()
        if len(estudios) != len(toma.estudio_ids):
            raise ValueError("Todos los estudios deben pertenecer a esta solicitud de laboratorio")
        if any(estudio.estado != "pendiente_muestra" for estudio in estudios):
            raise ValueError("Uno o más estudios ya tienen muestra o avanzaron de estado")
        if any(estudio.paciente_id != solicitud.paciente_id for estudio in estudios):
            raise ValueError("Los estudios deben pertenecer al paciente de la solicitud")

        referencia = f"MUE-{uuid4().hex[:10].upper()}"
        muestra = Muestra(
            referencia_muestra=referencia,
            paciente_id=solicitud.paciente_id,
            fecha_toma_real=toma.fecha_toma,
            hora_toma_real=toma.hora_toma,
            hora_no_registrada=toma.hora_no_registrada,
            fecha_hora_ingreso_sistema=datetime.now(timezone.utc),
            tipo_muestra=toma.tipo_muestra.strip(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=usuario_id,
            updated_by=usuario_id,
        )
        self.db.add(muestra)
        await self.db.flush()
        for estudio in estudios:
            self.db.add(MuestraEstudio(muestra_id=muestra.id, estudio_id=estudio.id))
            estudio.estado = "resultado_en_preparacion"
            estudio.updated_by = usuario_id
            estudio.updated_at = datetime.now(timezone.utc)
        self.db.add(AuditoriaAccion(
            fecha_hora=datetime.now(timezone.utc),
            usuario_id=usuario_id,
            accion=AccionAuditoria.CREAR,
            entidad_afectada="muestra",
            referencia_registro=referencia,
            detalle={"solicitud_id": solicitud.id, "estudio_ids": list(toma.estudio_ids)},
        ))
        await self.db.flush()
        return referencia

    async def obtener_resultado(self, estudio_id: int) -> ResultadoEstudio:
        fila = (await self.db.execute(
            select(
                EstudioSolicitado,
                TipoEstudio.nombre.label("estudio_nombre"),
                Paciente.nombre_completo.label("paciente_nombre"),
                TipoEstudio.plantilla_examen_id,
            )
            .join(TipoEstudio, TipoEstudio.id == EstudioSolicitado.tipo_estudio_id)
            .join(Paciente, Paciente.id == EstudioSolicitado.paciente_id)
            .join(Servicio, Servicio.id == EstudioSolicitado.servicio_id)
            .where(EstudioSolicitado.id == estudio_id, Servicio.codigo == "LAB")
        )).one_or_none()
        if fila is None:
            raise ValueError("El estudio no existe en el laboratorio")

        estudio, nombre, paciente_nombre, plantilla_id = fila
        version_plantilla = None
        parametros: list[ParametroResultado] = []
        if plantilla_id is not None:
            version_plantilla = (await self.db.execute(
                select(PlantillaExamenVersion)
                .where(
                    PlantillaExamenVersion.plantilla_examen_id == plantilla_id,
                    PlantillaExamenVersion.estado == "activa",
                )
                .order_by(PlantillaExamenVersion.numero_version.desc())
                .limit(1)
            )).scalar_one_or_none()

        resultado = (await self.db.execute(
            select(ResultadoLaboratorio).where(ResultadoLaboratorio.estudio_id == estudio_id)
        )).scalar_one_or_none()
        version = None
        if resultado is not None:
            version = (await self.db.execute(
                select(VersionResultado)
                .where(VersionResultado.resultado_id == resultado.id)
                .order_by(VersionResultado.numero_version.desc())
                .limit(1)
            )).scalar_one_or_none()
            # Cada resultado conserva la versión de formato con la que se creó.
            version_plantilla = await self.db.get(
                PlantillaExamenVersion, resultado.plantilla_version_id
            )

        if version_plantilla is not None:
            filas_parametros = (await self.db.execute(
                select(ParametroPlantilla, SeccionPlantilla.nombre.label("seccion"))
                .outerjoin(SeccionPlantilla, SeccionPlantilla.id == ParametroPlantilla.seccion_id)
                .where(ParametroPlantilla.plantilla_version_id == version_plantilla.id)
                .order_by(SeccionPlantilla.orden, ParametroPlantilla.orden)
            )).all()
            valores = {}
            if version is not None:
                detalles = (await self.db.execute(
                    select(DetalleValorResultado).where(
                        DetalleValorResultado.version_resultado_id == version.id
                    )
                )).scalars().all()
                for detalle in detalles:
                    valor = next((v for v in (
                        detalle.valor_entero, detalle.valor_decimal,
                        detalle.valor_texto, detalle.valor_cualitativo,
                    ) if v is not None), None)
                    if valor is not None:
                        valores[detalle.parametro_id] = str(valor)
            parametros = [
                ParametroResultado(
                    id=param.id,
                    codigo=param.codigo,
                    nombre=param.nombre,
                    tipo_entrada=param.tipo_entrada,
                    unidad=param.unidad,
                    rango_referencia=param.rango_referencia_texto,
                    obligatorio=param.obligatorio,
                    orden=param.orden,
                    seccion=seccion,
                    valor=valores.get(param.id),
                )
                for param, seccion in filas_parametros
            ]

        return ResultadoEstudio(
            estudio_id=estudio.id,
            referencia_estudio=estudio.referencia,
            paciente_nombre=paciente_nombre,
            tipo_estudio_nombre=nombre,
            estado_estudio=estudio.estado,
            estado_resultado=version.estado if version else None,
            numero_version=version.numero_version if version else None,
            plantilla_configurada=version_plantilla is not None and bool(parametros),
            observaciones=resultado.observaciones_generales if resultado else None,
            parametros=tuple(parametros),
        )

    async def guardar_borrador(
        self,
        estudio_id: int,
        valores: tuple[ValorResultadoEntrada, ...],
        observaciones: str | None,
        usuario_id: int,
    ) -> BorradorResultado:
        estudio = (await self.db.execute(
            select(EstudioSolicitado)
            .where(EstudioSolicitado.id == estudio_id)
            .with_for_update()
        )).scalar_one_or_none()
        if estudio is None or estudio.estado != "resultado_en_preparacion":
            raise ValueError("El estudio no está disponible para capturar resultados")
        tipo = await self.db.get(TipoEstudio, estudio.tipo_estudio_id)
        resultado = (await self.db.execute(
            select(ResultadoLaboratorio).where(ResultadoLaboratorio.estudio_id == estudio_id)
        )).scalar_one_or_none()
        if resultado is None:
            plantilla = (await self.db.execute(
                select(PlantillaExamenVersion)
                .where(
                    PlantillaExamenVersion.plantilla_examen_id == tipo.plantilla_examen_id,
                    PlantillaExamenVersion.estado == "activa",
                )
                .order_by(PlantillaExamenVersion.numero_version.desc())
                .limit(1)
            )).scalar_one_or_none()
            if plantilla is None:
                raise ValueError("Este estudio todavía no tiene una plantilla de resultados activa")
            resultado = ResultadoLaboratorio(
                estudio_id=estudio_id,
                plantilla_version_id=plantilla.id,
                observaciones_generales=observaciones,
                created_by=usuario_id,
                updated_by=usuario_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(resultado)
            await self.db.flush()
            version = VersionResultado(
                resultado_id=resultado.id,
                numero_version=1,
                estado="borrador",
                created_by=usuario_id,
                updated_by=usuario_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(version)
            await self.db.flush()
        else:
            version = (await self.db.execute(
                select(VersionResultado)
                .where(VersionResultado.resultado_id == resultado.id)
                .order_by(VersionResultado.numero_version.desc())
                .limit(1)
            )).scalar_one()
            if version.estado != "borrador":
                raise ValueError("El resultado publicado no se puede sobrescribir")
            resultado.observaciones_generales = observaciones
            resultado.updated_by = usuario_id
            resultado.updated_at = datetime.now(timezone.utc)
            version.updated_by = usuario_id
            version.updated_at = datetime.now(timezone.utc)
        parametros = (await self.db.execute(
            select(ParametroPlantilla).where(
                ParametroPlantilla.plantilla_version_id == resultado.plantilla_version_id
            )
        )).scalars().all()
        por_id = {param.id: param for param in parametros}
        detalles_existentes = (await self.db.execute(
            select(DetalleValorResultado).where(
                DetalleValorResultado.version_resultado_id == version.id
            )
        )).scalars().all()
        detalle_por_parametro = {detalle.parametro_id: detalle for detalle in detalles_existentes}
        if len({valor.parametro_id for valor in valores}) != len(valores):
            raise ValueError("No repitas parámetros en el resultado")
        for entrada in valores:
            parametro = por_id.get(entrada.parametro_id)
            if parametro is None:
                raise ValueError("El resultado contiene un parámetro ajeno a su formato")
            valor = entrada.valor.strip() if entrada.valor is not None else ""
            campos = {
                "valor_entero": None,
                "valor_decimal": None,
                "valor_texto": None,
                "valor_cualitativo": None,
            }
            if valor:
                try:
                    if parametro.tipo_entrada == "entero":
                        campos["valor_entero"] = int(valor)
                    elif parametro.tipo_entrada == "decimal":
                        decimal = Decimal(valor.replace(",", "."))
                        if not decimal.is_finite():
                            raise InvalidOperation
                        campos["valor_decimal"] = decimal
                    elif parametro.tipo_entrada in ("texto", "rango"):
                        campos["valor_texto"] = valor
                    elif parametro.tipo_entrada == "cualitativo":
                        campos["valor_cualitativo"] = valor
                    else:
                        raise ValueError("Tipo de parámetro no compatible")
                except (InvalidOperation, ValueError):
                    raise ValueError(f"El valor de {parametro.nombre} no tiene el formato esperado") from None

            detalle = detalle_por_parametro.get(parametro.id)
            if detalle is None:
                detalle = DetalleValorResultado(
                    version_resultado_id=version.id,
                    parametro_id=parametro.id,
                    fuera_de_rango=False,
                )
                self.db.add(detalle)
            for campo, campo_valor in campos.items():
                setattr(detalle, campo, campo_valor)
            detalle.fuera_de_rango = False
        self.db.add(AuditoriaAccion(
            fecha_hora=datetime.now(timezone.utc),
            usuario_id=usuario_id,
            accion=AccionAuditoria.MODIFICAR,
            entidad_afectada="resultado_laboratorio",
            referencia_registro=estudio.referencia,
            detalle={"numero_version": version.numero_version},
        ))
        await self.db.flush()
        return BorradorResultado(estudio_id, version.estado, version.numero_version)

    async def publicar_resultado(self, estudio_id: int, usuario_id: int) -> BorradorResultado:
        estudio = (await self.db.execute(
            select(EstudioSolicitado)
            .where(EstudioSolicitado.id == estudio_id)
            .with_for_update()
        )).scalar_one_or_none()
        if estudio is None or estudio.estado != "resultado_en_preparacion":
            raise ValueError("El estudio no está disponible para publicación")
        resultado = (await self.db.execute(
            select(ResultadoLaboratorio).where(ResultadoLaboratorio.estudio_id == estudio_id)
        )).scalar_one_or_none()
        if resultado is None:
            raise ValueError("Guarda primero el borrador del resultado")
        version = (await self.db.execute(
            select(VersionResultado)
            .where(VersionResultado.resultado_id == resultado.id)
            .order_by(VersionResultado.numero_version.desc())
            .limit(1)
        )).scalar_one_or_none()
        if version is None or version.estado != "borrador":
            raise ValueError("No hay un borrador pendiente de revisión")
        parametros = (await self.db.execute(
            select(ParametroPlantilla).where(
                ParametroPlantilla.plantilla_version_id == resultado.plantilla_version_id
            )
        )).scalars().all()
        detalles = (await self.db.execute(
            select(DetalleValorResultado).where(
                DetalleValorResultado.version_resultado_id == version.id
            )
        )).scalars().all()
        faltantes = campos_obligatorios_faltantes(parametros, detalles)
        if faltantes:
            raise ValueError("Faltan campos obligatorios: " + ", ".join(faltantes))
        version.estado = "publicado"
        version.usuario_publicacion_id = usuario_id
        version.fecha_hora_publicacion = datetime.now(timezone.utc)
        version.updated_by = usuario_id
        version.updated_at = datetime.now(timezone.utc)
        estudio.estado = "publicado"
        estudio.updated_by = usuario_id
        estudio.updated_at = datetime.now(timezone.utc)
        self.db.add(AuditoriaAccion(
            fecha_hora=datetime.now(timezone.utc),
            usuario_id=usuario_id,
            accion=AccionAuditoria.PUBLICAR,
            entidad_afectada="resultado_laboratorio",
            referencia_registro=estudio.referencia,
            detalle={"numero_version": version.numero_version},
        ))
        await self.db.flush()
        return BorradorResultado(estudio_id, version.estado, version.numero_version)
