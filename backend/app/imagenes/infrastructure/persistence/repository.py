"""Persistencia del modulo de imagen: ecografia clinica y asistencia RAG."""
import hashlib
import json
import uuid
import uuid as uuid_lib
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select, text
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
            raise ValueError('El paciente no existe o estÃƒÂ¡ inactivo')

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
            raise ValueError('Uno o mÃƒÂ¡s estudios no estÃƒÂ¡n en el catÃƒÂ¡logo de imagen')

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
                # Solo el servicio de imagen: sin este filtro, los análisis de laboratorio
                # publicados aparecían en la ficha como si fueran ecografías.
                .join(Servicio, Servicio.id == TipoEstudio.servicio_id)
                .where(
                    EstudioSolicitado.paciente_id == paciente_id,
                    EstudioSolicitado.estado == 'publicado',
                    Servicio.codigo == 'IMG',
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
# ---------- asistencia radiológica local (RAG) ----------

PROPIETARIO = '''FROM public.estudio_solicitado e
    JOIN public.solicitud s ON s.id=e.solicitud_id
    JOIN public.medico m ON m.id=s.medico_solicitante_id
    JOIN public.usuario u ON u.trabajador_id=m.trabajador_id AND u.id=:usuario
    JOIN public.servicio v ON v.id=e.servicio_id AND v.codigo='IMG'
    JOIN public.tipo_estudio t ON t.id=e.tipo_estudio_id
    JOIN public.paciente p ON p.id=e.paciente_id
    WHERE u.estado='activo' '''


class EstudiosRepository:
    def __init__(self, db):
        self.db = db

    async def recuperar_interrumpidos(self):
        # Solo llamar tras adquirir liderazgo exclusivo de trabajos en PostgreSQL.
        await self.db.execute(text("UPDATE public.imagen_analisis_ia SET estado='interrumpido',error_codigo='reinicio',actualizado_en=now() WHERE estado='procesando'"))

    async def reclamar(self):
        row = (await self.db.execute(text('''UPDATE public.imagen_analisis_ia
            SET estado='procesando',actualizado_en=now()
            WHERE id=(SELECT id FROM public.imagen_analisis_ia WHERE estado='en_cola'
            ORDER BY creado_en,id FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *'''))).mappings().first()
        return dict(row) if row else None

    async def listar(self, usuario_id: int, pagina: int = 1):
        if pagina < 1:
            raise ValueError('PÃ¡gina invÃ¡lida.')
        rows = await self.db.execute(text('''SELECT e.id,e.referencia,e.estado,t.nombre AS estudio,
            p.codigo_paciente,p.nombre_completo AS paciente ''' + PROPIETARIO + '''
            AND e.estado='publicado' ORDER BY e.id DESC LIMIT 20 OFFSET :offset'''),
            {'usuario':usuario_id,'offset':(pagina-1)*20})
        return [dict(r) for r in rows.mappings()]

    async def obtener(self, estudio_id: int, usuario_id: int):
        row = (await self.db.execute(text('''SELECT e.id,e.referencia,t.nombre AS estudio,
            p.codigo_paciente,p.nombre_completo AS paciente ''' + PROPIETARIO + '''
            AND e.id=:id AND e.estado='publicado' '''), {'usuario':usuario_id,'id':estudio_id})).mappings().first()
        if row is None:
            return None
        informe = (await self.db.execute(text('''SELECT id AS informe_id,numero_version,
            COALESCE(descripcion_texto,'') AS informe_texto FROM public.informe_imagen
            WHERE estudio_id=:id AND estado='publicado' ORDER BY numero_version DESC LIMIT 1'''), {'id':estudio_id})).mappings().first()
        if informe is None:
            return dict(row) | {'informe_id':None,'informe_texto':'','archivo':None}
        archivo = (await self.db.execute(text('''SELECT id,nombre_original,url_archivo,mime_type,
            tamano_bytes,hash_sha256,activo FROM public.archivo_imagen
            WHERE informe_id=:id AND activo ORDER BY id DESC LIMIT 1'''), {'id':informe['informe_id']})).mappings().first()
        ultimo = await self.db.scalar(text('''SELECT id FROM public.imagen_analisis_ia
            WHERE estudio_id=:id AND informe_id=:informe AND solicitado_por=:usuario
            ORDER BY creado_en DESC,id DESC LIMIT 1'''),
            {'id':estudio_id,'informe':informe['informe_id'],'usuario':usuario_id})
        return dict(row) | dict(informe) | {'archivo': dict(archivo) if archivo else None,'analisis_reciente':ultimo}

    async def crear_analisis(self, snapshot: dict, usuario_id: int, clave: str, proyeccion: str):
        if not clave or len(clave)>100 or proyeccion not in ('PA','AP','frontal_no_especificada'):
            raise ValueError('Solicitud de anÃ¡lisis invÃ¡lida.')
        if not snapshot.get('archivo') or not snapshot.get('informe_id'):
            raise ValueError('El estudio necesita informe publicado y archivo activo.')
        await self.db.execute(text('SELECT pg_advisory_xact_lock(:id)'), {'id': snapshot['id']})
        existente = (await self.db.execute(text('SELECT * FROM public.imagen_analisis_ia WHERE solicitado_por=:u AND clave=:c'), {'u':usuario_id,'c':clave})).mappings().first()
        sha = hashlib.sha256(snapshot['informe_texto'].encode()).hexdigest()
        if existente:
            if (existente['estudio_id'],existente['informe_id'],existente['archivo_id'],existente['proyeccion'],existente['informe_sha256'],existente['archivo_sha256']) != (
                snapshot['id'],snapshot['informe_id'],snapshot['archivo']['id'],proyeccion,sha,snapshot['archivo']['hash_sha256']):
                raise ValueError('La clave de reintento ya corresponde a otros datos.')
            return dict(existente)
        activo = await self.db.scalar(text("SELECT 1 FROM public.imagen_analisis_ia WHERE estudio_id=:id AND estado IN ('en_cola','procesando')"), {'id':snapshot['id']})
        if activo:
            raise ValueError('Ya hay un anÃ¡lisis activo para este estudio.')
        row = (await self.db.execute(text('''INSERT INTO public.imagen_analisis_ia
            (id,estudio_id,informe_id,archivo_id,solicitado_por,clave,proyeccion,informe_texto,informe_sha256,archivo_sha256)
            VALUES (CAST(:id AS uuid),:e,:i,:a,:u,:c,:p,:texto,:sha,:ah) RETURNING *'''),
            {'id':str(uuid.uuid4()),'e':snapshot['id'],'i':snapshot['informe_id'],'a':snapshot['archivo']['id'],
             'u':usuario_id,'c':clave,'p':proyeccion,'texto':snapshot['informe_texto'],'sha':sha,'ah':snapshot['archivo']['hash_sha256']})).mappings().one()
        return dict(row)

    async def obtener_analisis(self, analisis_id, usuario_id: int):
        row = (await self.db.execute(text('SELECT * FROM public.imagen_analisis_ia WHERE id=CAST(:id AS uuid)'), {'id':str(analisis_id)})).mappings().first()
        if row is None or await self.obtener(row['estudio_id'], usuario_id) is None:
            return None
        revisiones = (await self.db.execute(text('''SELECT version,decision,motivo,correccion,fecha,usuario_id
            FROM public.imagen_revision_ia WHERE analisis_id=CAST(:id AS uuid) ORDER BY version'''), {'id':str(analisis_id)})).mappings()
        return dict(row) | {'revisiones':[dict(r) for r in revisiones]}

    async def finalizar(self, analisis_id, resultado: dict | None, error: str | None, liderazgo=None):
        fence = ''' AND EXISTS (SELECT 1 FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid
            WHERE l.locktype='advisory' AND l.classid=0 AND l.objid=2111009 AND l.objsubid=1
            AND l.granted AND l.pid=:lider_pid AND a.backend_start=:lider_inicio)''' if liderazgo else ''
        await self.db.execute(text('''UPDATE public.imagen_analisis_ia SET estado=:estado,
            resultado=CAST(:resultado AS jsonb),error_codigo=:error,actualizado_en=now()
            WHERE id=CAST(:id AS uuid) AND estado IN ('en_cola','procesando')''' + fence),
            {'id':str(analisis_id),'estado':'error' if error else 'completado',
             'resultado':json.dumps(resultado) if resultado is not None else None,'error':error,
             'lider_pid':liderazgo['pid'] if liderazgo else None,
             'lider_inicio':liderazgo['inicio'] if liderazgo else None})

    async def registrar_revision(self, analisis_id, usuario_id, version, decision, motivo, correccion):
        analisis = await self.obtener_analisis(analisis_id, usuario_id)
        if analisis is None:
            raise LookupError('AnÃ¡lisis no encontrado.')
        if (analisis['estado'] != 'completado' or decision not in ('aceptada_como_propuesta','corregida','rechazada')
                or (decision != 'aceptada_como_propuesta' and not motivo.strip())
                or (decision == 'corregida' and not (correccion or '').strip())):
            raise ValueError('La revisiÃ³n requiere anÃ¡lisis completo y datos obligatorios.')
        version_nueva = await self.db.scalar(text('''UPDATE public.imagen_analisis_ia
            SET version_revision=version_revision+1,actualizado_en=now()
            WHERE id=CAST(:id AS uuid) AND version_revision=:v RETURNING version_revision'''), {'id':str(analisis_id),'v':version})
        if version_nueva is None:
            raise ValueError('La revisiÃ³n cambiÃ³; recarga antes de guardar.')
        await self.db.execute(text('''INSERT INTO public.imagen_revision_ia
            (analisis_id,usuario_id,version,decision,motivo,correccion)
            VALUES (CAST(:id AS uuid),:u,:v,:d,:m,:c)'''),
            {'id':str(analisis_id),'u':usuario_id,'v':version_nueva,'d':decision,'m':motivo,'c':correccion})
        return await self.obtener_analisis(analisis_id, usuario_id)
