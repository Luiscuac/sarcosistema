"""Persistencia del modulo de imagen (ORM, igual que laboratorio)."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.imagenes.domain.entities import (
    ArchivoImagen,
    EstudioImagenDetalle,
    EstudioImagenPendiente,
    EstudioImagenPublicado,
    InformeImagen,
    SolicitudEcografia,
)
from app.laboratorio.infrastructure.persistence.models import (
    ArchivoImagen as ArchivoImagenTabla,
    AuditoriaAccion,
    EstudioSolicitado,
    InformeImagen as InformeImagenTabla,
    Servicio,
    Solicitud,
    TipoEstudio,
)
from app.shared.entities.paciente import Paciente


class RepositorioImagenSql:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- solicitud del medico ----------

    async def crear_solicitud(self, solicitud: SolicitudEcografia, usuario_id: int) -> int:
        paciente = await self.db.get(Paciente, solicitud.paciente_id)
        if paciente is None or paciente.estado != 'activo':
            raise ValueError('El paciente no existe o estÃ¡ inactivo')

        tipos = (
            await self.db.execute(
                select(TipoEstudio.id, TipoEstudio.nombre, TipoEstudio.servicio_id)
                .join(Servicio, Servicio.id == TipoEstudio.servicio_id)
                .where(
                    TipoEstudio.id.in_(solicitud.tipo_estudio_ids),
                    TipoEstudio.activo.is_(True),
                    Servicio.activo.is_(True),
                    Servicio.codigo == 'IMG',
                )
            )
        ).all()
        if len(tipos) != len(solicitud.tipo_estudio_ids):
            raise ValueError('Uno o mÃ¡s estudios no estÃ¡n en el catÃ¡logo de imagen')

        if solicitud.clave_idempotencia:
            existente = (
                await self.db.execute(
                    select(Solicitud.id).where(
                        Solicitud.clave_idempotencia == solicitud.clave_idempotencia
                    )
                )
            ).scalar_one_or_none()
            if existente is not None:
                return existente

        referencia = f"IMG-{datetime.now(timezone.utc):%y%m%d}-{uuid4().hex[:6].upper()}"
        modelo = Solicitud(
            referencia=referencia,
            paciente_id=solicitud.paciente_id,
            fecha_solicitud=datetime.now(timezone.utc),
            prioridad=solicitud.prioridad,
            clave_idempotencia=solicitud.clave_idempotencia or None,
            medico_solicitante_nombre_snapshot=solicitud.medico_solicitante_nombre,
            created_by=usuario_id,
        )
        self.db.add(modelo)
        await self.db.flush()

        for tipo_id in dict.fromkeys(solicitud.tipo_estudio_ids):
            self.db.add(EstudioSolicitado(
                referencia=f"{referencia}-{uuid4().hex[:4].upper()}",
                solicitud_id=modelo.id,
                paciente_id=solicitud.paciente_id,
                servicio_id=tipos_ids_to_servicio(tipos, tipo_id),
                tipo_estudio_id=tipo_id,
                estado='pendiente_muestra',
                created_by=usuario_id,
            ))
        self.db.add(AuditoriaAccion(
            fecha_hora=datetime.now(timezone.utc), usuario_id=usuario_id, accion='crear',
            entidad_afectada='solicitud', referencia_registro=str(modelo.id),
            detalle={'origen': 'imagenes'},
        ))
        await self.db.flush()
        return modelo.id

    # ---------- bandeja del radiologo ----------

    async def listar_catalogo_imagen(self) -> list[dict]:
        """Tipos de estudio de imagen activos que el medico puede solicitar."""
        filas = (
            await self.db.execute(
                select(TipoEstudio.id, TipoEstudio.codigo, TipoEstudio.nombre)
                .join(Servicio, Servicio.id == TipoEstudio.servicio_id)
                .where(
                    TipoEstudio.activo.is_(True),
                    Servicio.activo.is_(True),
                    Servicio.codigo == 'IMG',
                    TipoEstudio.requiere_archivos.is_(True),
                )
                .order_by(TipoEstudio.nombre)
            )
        ).all()
        return [
            {'id': fila.id, 'codigo': fila.codigo, 'nombre': fila.nombre}
            for fila in filas
        ]

    async def listar_bandeja(self) -> list[EstudioImagenPendiente]:
        filas = (
            await self.db.execute(
                select(EstudioSolicitado, Solicitud, Paciente, TipoEstudio)
                .join(Solicitud, Solicitud.id == EstudioSolicitado.solicitud_id)
                .join(Paciente, Paciente.id == EstudioSolicitado.paciente_id)
                .join(TipoEstudio, TipoEstudio.id == EstudioSolicitado.tipo_estudio_id)
                .join(Servicio, Servicio.id == EstudioSolicitado.servicio_id)
                .where(
                    Servicio.codigo == 'IMG',
                    EstudioSolicitado.estado.in_(['pendiente_muestra', 'resultado_en_preparacion']),
                )
                .order_by(EstudioSolicitado.id.desc())
            )
        ).all()
        return [
            EstudioImagenPendiente(
                estudio_id=estudio.id,
                referencia_estudio=estudio.referencia,
                referencia_solicitud=solicitud.referencia,
                paciente_id=estudio.paciente_id,
                paciente_nombre=paciente.nombre_completo,
                tipo_estudio_nombre=tipo.nombre,
                prioridad=solicitud.prioridad,
                estado=estudio.estado,
                fecha_solicitud=solicitud.fecha_solicitud,
            )
            for estudio, solicitud, paciente, tipo in filas
        ]

    async def obtener_estudio(self, estudio_id: int) -> EstudioImagenDetalle | None:
        fila = (
            await self.db.execute(
                select(EstudioSolicitado, Solicitud, Paciente, TipoEstudio)
                .join(Solicitud, Solicitud.id == EstudioSolicitado.solicitud_id)
                .join(Paciente, Paciente.id == EstudioSolicitado.paciente_id)
                .join(TipoEstudio, TipoEstudio.id == EstudioSolicitado.tipo_estudio_id)
                .join(Servicio, Servicio.id == EstudioSolicitado.servicio_id)
                .where(EstudioSolicitado.id == estudio_id, Servicio.codigo == 'IMG')
            )
        ).one_or_none()
        if fila is None:
            return None
        estudio, solicitud, paciente, tipo = fila
        return EstudioImagenDetalle(
            estudio_id=estudio.id,
            referencia_estudio=estudio.referencia,
            referencia_solicitud=solicitud.referencia,
            paciente_nombre=paciente.nombre_completo,
            tipo_estudio_nombre=tipo.nombre,
            estado=estudio.estado,
            fecha_solicitud=solicitud.fecha_solicitud,
            informe=await self._ultimo_informe(estudio_id),
        )

    async def _ultimo_informe(self, estudio_id: int) -> InformeImagen | None:
        informe = (
            await self.db.execute(
                select(InformeImagenTabla)
                .where(InformeImagenTabla.estudio_id == estudio_id)
                .order_by(InformeImagenTabla.numero_version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if informe is None:
            return None
        return await self._presentar_informe(informe)

    async def _presentar_informe(self, fila: InformeImagenTabla) -> InformeImagen:
        archivos = (
            await self.db.execute(
                select(ArchivoImagenTabla)
                .where(
                    ArchivoImagenTabla.informe_id == fila.id,
                    ArchivoImagenTabla.activo.is_(True),
                )
                .order_by(ArchivoImagenTabla.id)
            )
        ).scalars().all()
        return InformeImagen(
            id=fila.id,
            estudio_id=fila.estudio_id,
            numero_version=fila.numero_version,
            descripcion_texto=fila.descripcion_texto,
            estado=fila.estado,
            motivo_rectificacion=fila.motivo_rectificacion,
            fecha_hora_publicacion=fila.fecha_hora_publicacion,
            archivos=tuple(
                ArchivoImagen(
                    id=a.id, nombre_original=a.nombre_original, mime_type=a.mime_type,
                    tamano_bytes=a.tamano_bytes, hash_sha256=a.hash_sha256,
                    fecha_carga=a.fecha_carga, url_archivo=a.url_archivo,
                )
                for a in archivos
            ),
        )

    # ---------- subida y publicacion ----------

    async def guardar_informe(
        self, estudio_id: int, descripcion: str | None, archivos: list[dict], usuario_id: int
    ) -> tuple[InformeImagen, bool]:
        ultimo = (
            await self.db.execute(
                select(InformeImagenTabla)
                .where(InformeImagenTabla.estudio_id == estudio_id)
                .order_by(InformeImagenTabla.numero_version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if ultimo is not None and ultimo.estado == 'publicado':
            from app.imagenes.domain.errors import InformeYaPublicado

            raise InformeYaPublicado('El informe ya esta publicado; usa rectificar')

        numero = (ultimo.numero_version + 1) if ultimo is not None else 1
        informe = InformeImagenTabla(
            estudio_id=estudio_id,
            numero_version=numero,
            descripcion_texto=descripcion,
            estado='borrador',
            version_anterior_id=ultimo.id if ultimo is not None else None,
            created_by=usuario_id,
        )
        self.db.add(informe)
        await self.db.flush()

        for archivo in archivos:
            self.db.add(ArchivoImagenTabla(
                informe_id=informe.id,
                nombre_original=archivo['nombre_original'],
                url_archivo=archivo['url_archivo'],
                mime_type=archivo['mime_type'],
                tamano_bytes=archivo['tamano_bytes'],
                hash_sha256=archivo['hash_sha256'],
                fecha_carga=datetime.now(timezone.utc),
                created_by=usuario_id,
            ))

        estudio = await self.db.get(EstudioSolicitado, estudio_id)
        estudio.estado = 'resultado_en_preparacion'
        estudio.updated_by = usuario_id
        self.db.add(AuditoriaAccion(
            fecha_hora=datetime.now(timezone.utc), usuario_id=usuario_id, accion='modificar',
            entidad_afectada='informe_imagen', referencia_registro=str(estudio_id),
            detalle={'version': numero, 'archivos': len(archivos)},
        ))
        await self.db.flush()
        return await self._presentar_informe(informe), True

    async def publicar_informe(self, estudio_id: int, usuario_id: int) -> InformeImagen:
        informe = (
            await self.db.execute(
                select(InformeImagenTabla)
                .where(InformeImagenTabla.estudio_id == estudio_id)
                .order_by(InformeImagenTabla.numero_version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if informe is None:
            from app.imagenes.domain.errors import InformeSinContenido

            raise InformeSinContenido('No hay informe para publicar')

        informe.estado = 'publicado'
        informe.usuario_publicacion_id = usuario_id
        informe.fecha_hora_publicacion = datetime.now(timezone.utc)
        informe.updated_by = usuario_id

        estudio = await self.db.get(EstudioSolicitado, estudio_id)
        estudio.estado = 'publicado'
        estudio.updated_by = usuario_id
        self.db.add(AuditoriaAccion(
            fecha_hora=datetime.now(timezone.utc), usuario_id=usuario_id, accion='publicar',
            entidad_afectada='estudio_solicitado', referencia_registro=str(estudio_id),
            detalle={'version': informe.numero_version},
        ))
        await self.db.flush()
        return await self._presentar_informe(informe)

    # ---------- historial del paciente ----------

    async def listar_publicados_paciente(self, paciente_id: int) -> list[EstudioImagenPublicado]:
        filas = (
            await self.db.execute(
                select(EstudioSolicitado, Solicitud, TipoEstudio)
                .join(Solicitud, Solicitud.id == EstudioSolicitado.solicitud_id)
                .join(TipoEstudio, TipoEstudio.id == EstudioSolicitado.tipo_estudio_id)
                .where(
                    EstudioSolicitado.paciente_id == paciente_id,
                    EstudioSolicitado.estado == 'publicado',
                )
                .order_by(Solicitud.fecha_solicitud.desc(), EstudioSolicitado.id.desc())
            )
        ).all()
        publicados = []
        for estudio, solicitud, tipo in filas:
            informe = await self._ultimo_informe(estudio.id)
            publicados.append(EstudioImagenPublicado(
                estudio_id=estudio.id,
                referencia_estudio=estudio.referencia,
                tipo_estudio_nombre=tipo.nombre,
                fecha_solicitud=solicitud.fecha_solicitud,
                fecha_publicacion=informe.fecha_hora_publicacion if informe else None,
                descripcion_texto=informe.descripcion_texto if informe else None,
                archivos=informe.archivos if informe else (),
            ))
        return publicados

    async def obtener_archivo(self, archivo_id: int) -> ArchivoImagen | None:
        fila = (
            await self.db.execute(
                select(ArchivoImagenTabla)
                .where(ArchivoImagenTabla.id == archivo_id, ArchivoImagenTabla.activo.is_(True))
            )
        ).scalar_one_or_none()
        if fila is None:
            return None
        return ArchivoImagenTabla(
            id=fila.id, nombre_original=fila.nombre_original, mime_type=fila.mime_type,
            tamano_bytes=fila.tamano_bytes, hash_sha256=fila.hash_sha256,
            fecha_carga=fila.fecha_carga, url_archivo=fila.url_archivo,
        )

    async def obtener_estudio_de_archivo(self, archivo_id: int) -> EstudioImagenDetalle | None:
        """Estudio al que pertenece un archivo, para autorizar la descarga."""
        informe_id = (
            await self.db.execute(
                select(ArchivoImagenTabla.informe_id).where(ArchivoImagenTabla.id == archivo_id)
            )
        ).scalar_one_or_none()
        if informe_id is None:
            return None
        estudio_id = (
            await self.db.execute(
                select(InformeImagenTabla.estudio_id).where(InformeImagenTabla.id == informe_id)
            )
        ).scalar_one_or_none()
        return await self.obtener_estudio(estudio_id)


def tipos_ids_to_servicio(tipos, tipo_id) -> int:
    return next(t.servicio_id for t in tipos if t.id == tipo_id)
