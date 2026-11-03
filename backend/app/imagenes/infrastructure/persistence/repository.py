import hashlib
import json
import uuid

from sqlalchemy import text

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
        return dict(row) | dict(informe) | {'archivo': dict(archivo) if archivo else None}

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

    async def obtener_analisis(self, analisis_id, usuario_id: int):
        row = (await self.db.execute(text('SELECT * FROM public.imagen_analisis_ia WHERE id=CAST(:id AS uuid)'), {'id':str(analisis_id)})).mappings().first()
        if row is None or await self.obtener(row['estudio_id'], usuario_id) is None:
            return None
        revisiones = (await self.db.execute(text('''SELECT version,decision,motivo,correccion,fecha,usuario_id
            FROM public.imagen_revision_ia WHERE analisis_id=CAST(:id AS uuid) ORDER BY version'''), {'id':str(analisis_id)})).mappings()
        return dict(row) | {'revisiones':[dict(r) for r in revisiones]}

    async def finalizar(self, analisis_id, resultado: dict | None, error: str | None):
        await self.db.execute(text('''UPDATE public.imagen_analisis_ia SET estado=:estado,
            resultado=CAST(:resultado AS jsonb),error_codigo=:error,actualizado_en=now()
            WHERE id=CAST(:id AS uuid) AND estado IN ('en_cola','procesando')'''),
            {'id':str(analisis_id),'estado':'error' if error else 'completado',
             'resultado':json.dumps(resultado) if resultado is not None else None,'error':error})

    async def registrar_revision(self, analisis_id, usuario_id, version, decision, motivo, correccion):
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
            (analisis_id,usuario_id,version,decision,motivo,correccion)
            VALUES (CAST(:id AS uuid),:u,:v,:d,:m,:c)'''),
            {'id':str(analisis_id),'u':usuario_id,'v':version_nueva,'d':decision,'m':motivo,'c':correccion})
        return await self.obtener_analisis(analisis_id, usuario_id)
