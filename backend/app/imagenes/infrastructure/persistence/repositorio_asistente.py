"""Persistencia SQL del asistente radiologico y su cola de trabajos."""
import hashlib
import json
import uuid

from sqlalchemy import text

# ---------- asistencia radiológica local (RAG) ----------

# Solicitudes antiguas guardaron solo el nombre del médico (medico_solicitante_id nulo):
# en ese caso se reconoce al médico por el usuario que creó la solicitud.
PROPIETARIO = '''FROM public.estudio_solicitado e
    JOIN public.solicitud s ON s.id=e.solicitud_id
    JOIN public.usuario u ON u.id=:usuario
    JOIN public.medico m ON m.trabajador_id=u.trabajador_id
    JOIN public.servicio v ON v.id=e.servicio_id AND v.codigo='IMG'
    JOIN public.tipo_estudio t ON t.id=e.tipo_estudio_id
    JOIN public.paciente p ON p.id=e.paciente_id
    WHERE u.estado='activo' AND m.activo  -- cualquier médico activo, sin importar quién solicitó
    AND t.codigo = 'RX_TORAX' '''  # la asistencia IA solo analiza radiografía de tórax


class EstudiosRepository:
    def __init__(self, db):
        self.db = db

    async def recuperar_interrumpidos(self):
        # Solo llamar tras adquirir liderazgo exclusivo de trabajos en PostgreSQL.
        await self.db.execute(text("UPDATE public.imagen_analisis_ia SET estado='interrumpido',error_codigo='reinicio',actualizado_en=now() WHERE estado='procesando'"))
        # El triaje interrumpido vuelve a la cola: nadie lo pidió y no tiene revisiones asociadas.
        await self.db.execute(text("UPDATE public.imagen_triaje_ia SET estado='en_cola',actualizado_en=now() WHERE estado='procesando'"))

    async def reclamar(self):
        """Primero lo que pidió un médico (interactivo); después el triaje automático."""
        row = (await self.db.execute(text('''UPDATE public.imagen_analisis_ia
            SET estado='procesando',actualizado_en=now()
            WHERE id=(SELECT id FROM public.imagen_analisis_ia WHERE estado='en_cola'
            ORDER BY creado_en,id FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *'''))).mappings().first()
        if row:
            return dict(row) | {'tipo': 'analisis'}
        row = (await self.db.execute(text('''UPDATE public.imagen_triaje_ia
            SET estado='procesando',actualizado_en=now()
            WHERE id=(SELECT id FROM public.imagen_triaje_ia WHERE estado='en_cola'
            ORDER BY creado_en,id FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *'''))).mappings().first()
        return dict(row) | {'tipo': 'triaje'} if row else None

    async def archivo_de_triaje(self, trabajo: dict):
        row = (await self.db.execute(text('''SELECT a.id,a.nombre_original,a.url_archivo,a.mime_type,
            a.tamano_bytes,a.hash_sha256,a.activo FROM public.archivo_imagen a
            JOIN public.informe_imagen i ON i.id=a.informe_id
            WHERE a.id=:archivo AND i.estudio_id=:estudio'''),
            {'archivo': trabajo['archivo_id'], 'estudio': trabajo['estudio_id']})).mappings().first()
        if row is None or not row['activo'] or row['hash_sha256'] != trabajo['archivo_sha256']:
            raise ValueError('El archivo del triaje cambió o ya no está activo.')
        return dict(row)

    async def finalizar_triaje(self, triaje_id, resultado: dict | None, error: str | None, liderazgo=None):
        fence = ''' AND EXISTS (SELECT 1 FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid
            WHERE l.locktype='advisory' AND l.classid=0 AND l.objid=2111009 AND l.objsubid=1
            AND l.granted AND l.pid=:lider_pid AND a.backend_start=:lider_inicio)''' if liderazgo else ''
        await self.db.execute(text('''UPDATE public.imagen_triaje_ia SET estado=:estado,
            resultado=CAST(:resultado AS jsonb),error_codigo=:error,actualizado_en=now()
            WHERE id=CAST(:id AS uuid) AND estado IN ('en_cola','procesando')''' + fence),
            {'id':str(triaje_id),'estado':'error' if error else 'completado',
             'resultado':json.dumps(resultado) if resultado is not None else None,'error':error,
             'lider_pid':liderazgo['pid'] if liderazgo else None,
             'lider_inicio':liderazgo['inicio'] if liderazgo else None})

    async def listar(self, usuario_id: int, pagina: int = 1):
        if pagina < 1:
            raise ValueError('Página inválida.')
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
            raise ValueError('Solicitud de análisis inválida.')
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
            raise ValueError('Ya hay un análisis activo para este estudio.')
        row = (await self.db.execute(text('''INSERT INTO public.imagen_analisis_ia
            (id,estudio_id,informe_id,archivo_id,solicitado_por,clave,proyeccion,informe_texto,informe_sha256,archivo_sha256)
            VALUES (CAST(:id AS uuid),:e,:i,:a,:u,:c,:p,:texto,:sha,:ah) RETURNING *'''),
            {'id':str(uuid.uuid4()),'e':snapshot['id'],'i':snapshot['informe_id'],'a':snapshot['archivo']['id'],
             'u':usuario_id,'c':clave,'p':proyeccion,'texto':snapshot['informe_texto'],'sha':sha,'ah':snapshot['archivo']['hash_sha256']})).mappings().one()
        return dict(row)

    async def serie_triaje_paciente(self, estudio_id: int) -> list[dict]:
        """Triaje de las radiografías de tórax del mismo paciente hasta este estudio (incluido), más reciente primero.

        Una fila por estudio (la radiografía activa con mayor índice, como la bandeja). Los anteriores deben estar
        publicados; no se devuelven nombres ni textos del paciente. La autorización del estudio la hace el router.
        """
        filas = await self.db.execute(text('''WITH actual AS (
                SELECT e.id, e.paciente_id, s.fecha_solicitud FROM public.estudio_solicitado e
                JOIN public.solicitud s ON s.id=e.solicitud_id WHERE e.id=:id),
            candidatos AS (
                SELECT DISTINCT ON (e.id) e.id AS estudio_id, e.referencia, a.fecha_carga AS fecha,
                    s.fecha_solicitud,
                    (tr.resultado->'indice_pulmonar'->>'valor')::float AS indice,
                    tr.resultado->'indice_pulmonar'->>'version' AS indice_version,
                    (tr.resultado->'patron_tb'->>'valor')::float AS patron_tb_valor,
                    tr.resultado->'patron_tb'->>'nivel' AS patron_tb_nivel,
                    tr.resultado->'patron_tb'->>'version' AS patron_tb_version,
                    tr.resultado->'calidad'->>'estado' AS calidad,
                    tr.resultado->'all_findings' AS hallazgos
                FROM actual x
                JOIN public.estudio_solicitado e ON e.paciente_id=x.paciente_id
                JOIN public.solicitud s ON s.id=e.solicitud_id
                JOIN public.tipo_estudio t ON t.id=e.tipo_estudio_id AND t.codigo='RX_TORAX'
                JOIN public.imagen_triaje_ia tr ON tr.estudio_id=e.id AND tr.estado='completado'
                JOIN public.archivo_imagen a ON a.id=tr.archivo_id AND a.activo
                WHERE (e.id=x.id OR (e.estado='publicado'
                       AND (s.fecha_solicitud, e.id) < (x.fecha_solicitud, x.id)))
                ORDER BY e.id, (tr.resultado->'indice_pulmonar'->>'valor')::float DESC NULLS LAST)
            SELECT * FROM candidatos ORDER BY (estudio_id=:id) DESC, fecha_solicitud DESC, estudio_id DESC
            LIMIT 7'''), {'id': estudio_id})
        return [dict(f) for f in filas.mappings()]

    async def filas_concordancia(self) -> list[dict]:
        """Un registro por análisis con su última revisión. Solo agregables: sin pacientes ni texto."""
        filas = await self.db.execute(text('''WITH ultima AS (
                SELECT DISTINCT ON (analisis_id) analisis_id, decision, anormal_confirmado, tb_confirmada
                FROM public.imagen_revision_ia ORDER BY analisis_id, version DESC)
            SELECT a.estado, u.decision, u.anormal_confirmado, u.tb_confirmada,
                (a.resultado->'vision'->'indice_pulmonar'->>'valor')::float AS indice,
                (a.resultado->'vision'->'patron_tb'->>'valor')::float AS patron_tb,
                a.resultado->'vision'->'patron_tb'->>'version' AS patron_tb_version,
                jsonb_array_length(COALESCE(a.resultado->'fusion'->'discrepancias','[]'::jsonb)) AS discrepancias,
                jsonb_array_length(COALESCE(a.resultado->'fusion'->'posibles_omisiones','[]'::jsonb)) AS omisiones,
                jsonb_array_length(COALESCE(a.resultado->'fusion'->'coincidencias','[]'::jsonb)) AS coincidencias
            FROM public.imagen_analisis_ia a LEFT JOIN ultima u ON u.analisis_id=a.id'''))
        return [dict(f) for f in filas.mappings()]

    async def obtener_analisis(self, analisis_id, usuario_id: int):
        row = (await self.db.execute(text('SELECT * FROM public.imagen_analisis_ia WHERE id=CAST(:id AS uuid)'), {'id':str(analisis_id)})).mappings().first()
        if row is None or await self.obtener(row['estudio_id'], usuario_id) is None:
            return None
        revisiones = (await self.db.execute(text('''SELECT version,decision,motivo,correccion,anormal_confirmado,tb_confirmada,fecha,usuario_id
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

    async def registrar_revision(self, analisis_id, usuario_id, version, decision, motivo, correccion, anormal_confirmado=None,
                                 tb_confirmada=None):
        analisis = await self.obtener_analisis(analisis_id, usuario_id)
        if analisis is None:
            raise LookupError('Análisis no encontrado.')
        if (analisis['estado'] != 'completado' or decision not in ('aceptada_como_propuesta','corregida','rechazada')
                or (decision != 'aceptada_como_propuesta' and not motivo.strip())
                or (decision == 'corregida' and not (correccion or '').strip())):
            raise ValueError('La revisión requiere análisis completo y datos obligatorios.')
        version_nueva = await self.db.scalar(text('''UPDATE public.imagen_analisis_ia
            SET version_revision=version_revision+1,actualizado_en=now()
            WHERE id=CAST(:id AS uuid) AND version_revision=:v RETURNING version_revision'''), {'id':str(analisis_id),'v':version})
        if version_nueva is None:
            raise ValueError('La revisión cambió; recarga antes de guardar.')
        await self.db.execute(text('''INSERT INTO public.imagen_revision_ia
            (analisis_id,usuario_id,version,decision,motivo,correccion,anormal_confirmado,tb_confirmada)
            VALUES (CAST(:id AS uuid),:u,:v,:d,:m,:c,:anormal,:tb)'''),
            {'id':str(analisis_id),'u':usuario_id,'v':version_nueva,'d':decision,'m':motivo,'c':correccion,
             'anormal':anormal_confirmado,'tb':tb_confirmada})
        return await self.obtener_analisis(analisis_id, usuario_id)

