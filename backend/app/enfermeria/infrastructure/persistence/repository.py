from sqlalchemy import text

from app.enfermeria.domain.entities import CAMPOS_REGISTRO


PACIENTE_SELECT = '''p.id, p.codigo_paciente, p.historia_clinica, p.codigo_externo,
    p.nombre_completo, p.tipo_documento, p.numero_documento, p.fecha_nacimiento,
    p.sexo, p.estado'''

REGISTRO_SELECT = '''r.id, r.paciente_id, r.estado, r.motivo_consulta, r.sintomas,
    r.observaciones_enfermeria, r.peso_kg, r.talla_cm, r.temperatura_c,
    r.frecuencia_cardiaca, r.frecuencia_respiratoria, r.presion_sistolica,
    r.presion_diastolica, r.saturacion_oxigeno, r.dolor_escala, r.creado_en,
    r.publicado_en, u.identificador_acceso AS registrado_por,
    up.identificador_acceso AS publicado_por'''


class SqlAlchemyRegistroEnfermeriaRepository:
    def __init__(self, db):
        self.db = db

    async def buscar_pacientes(self, buscar: str, pagina: int, limite: int):
        params = {'buscar': buscar, 'limite': limite, 'offset': (pagina - 1) * limite}
        filtro = '''p.estado = 'activo' AND (
            strpos(lower(p.nombre_completo), lower(:buscar)) > 0 OR
            strpos(lower(coalesce(p.numero_documento, '')), lower(:buscar)) > 0 OR
            strpos(lower(p.codigo_paciente), lower(:buscar)) > 0 OR
            strpos(lower(coalesce(p.historia_clinica, '')), lower(:buscar)) > 0 OR
            strpos(lower(coalesce(p.codigo_externo, '')), lower(:buscar)) > 0)'''
        total = (await self.db.execute(text(
            f'SELECT count(*) FROM public.paciente p WHERE {filtro}'
        ), params)).scalar_one()
        filas = (await self.db.execute(text(f'''
            SELECT {PACIENTE_SELECT} FROM public.paciente p WHERE {filtro}
            ORDER BY p.nombre_completo, p.id LIMIT :limite OFFSET :offset
        '''), params)).mappings().all()
        return {'items': [dict(fila) for fila in filas], 'total': total,
                'pagina': pagina, 'limite': limite}

    async def obtener_paciente(self, paciente_id: int):
        fila = (await self.db.execute(text(f'''
            SELECT {PACIENTE_SELECT} FROM public.paciente p
            WHERE p.id = :id AND p.estado = 'activo'
        '''), {'id': paciente_id})).mappings().one_or_none()
        return dict(fila) if fila else None

    async def crear_borrador(self, paciente_id: int, usuario_id: int, datos):
        columnas = ', '.join(CAMPOS_REGISTRO)
        valores = ', '.join(f':{campo}' for campo in CAMPOS_REGISTRO)
        params = {'paciente_id': paciente_id, 'usuario_id': usuario_id, **datos.model_dump()}
        registro_id = (await self.db.execute(text(f'''
            INSERT INTO public.registro_enfermeria
                (paciente_id, registrado_por, {columnas})
            VALUES (:paciente_id, :usuario_id, {valores})
            RETURNING id
        '''), params)).scalar_one()
        await self._auditar(usuario_id, 'crear', registro_id)
        return await self._obtener(registro_id)

    async def editar_borrador(self, registro_id: int, usuario_id: int, datos):
        asignaciones = ', '.join(f'{campo} = :{campo}' for campo in CAMPOS_REGISTRO)
        params = {'id': registro_id, 'usuario_id': usuario_id, **datos.model_dump()}
        cambiado = (await self.db.execute(text(f'''
            UPDATE public.registro_enfermeria SET {asignaciones}
            WHERE id = :id AND registrado_por = :usuario_id AND estado = 'borrador'
            RETURNING id
        '''), params)).scalar_one_or_none()
        if cambiado is None:
            return None
        await self._auditar(usuario_id, 'modificar', registro_id)
        return await self._obtener(registro_id)

    async def publicar(self, registro_id: int, usuario_id: int):
        cambiado = (await self.db.execute(text('''
            UPDATE public.registro_enfermeria
            SET estado = 'publicado', publicado_por = :usuario_id, publicado_en = now()
            WHERE id = :id AND registrado_por = :usuario_id AND estado = 'borrador'
            RETURNING id
        '''), {'id': registro_id, 'usuario_id': usuario_id})).scalar_one_or_none()
        if cambiado is None:
            return None
        await self._auditar(usuario_id, 'publicar', registro_id)
        return await self._obtener(registro_id)

    async def listar_registros(self, paciente_id: int, usuario_id: int):
        filas = (await self.db.execute(text(f'''
            SELECT {REGISTRO_SELECT} FROM public.registro_enfermeria r
            JOIN public.usuario u ON u.id = r.registrado_por
            LEFT JOIN public.usuario up ON up.id = r.publicado_por
            WHERE r.paciente_id = :paciente_id AND r.registrado_por = :usuario_id
            ORDER BY r.creado_en DESC, r.id DESC
        '''), {'paciente_id': paciente_id, 'usuario_id': usuario_id})).mappings().all()
        return [dict(fila) for fila in filas]

    async def listar_publicados(self, paciente_id: int):
        filas = (await self.db.execute(text(f'''
            SELECT {REGISTRO_SELECT} FROM public.registro_enfermeria r
            JOIN public.usuario u ON u.id = r.registrado_por
            LEFT JOIN public.usuario up ON up.id = r.publicado_por
            WHERE r.paciente_id = :paciente_id AND r.estado = 'publicado'
            ORDER BY r.publicado_en DESC, r.id DESC
        '''), {'paciente_id': paciente_id})).mappings().all()
        return [dict(fila) for fila in filas]

    async def _obtener(self, registro_id: int):
        fila = (await self.db.execute(text(f'''
            SELECT {REGISTRO_SELECT} FROM public.registro_enfermeria r
            JOIN public.usuario u ON u.id = r.registrado_por
            LEFT JOIN public.usuario up ON up.id = r.publicado_por
            WHERE r.id = :id
        '''), {'id': registro_id})).mappings().one()
        return dict(fila)

    async def _auditar(self, usuario_id: int, accion: str, registro_id: int):
        await self.db.execute(text('''
            INSERT INTO public.auditoria_accion
                (fecha_hora, usuario_id, accion, entidad_afectada, referencia_registro)
            VALUES (now(), :usuario_id, :accion, 'registro_enfermeria', :referencia)
        '''), {'usuario_id': usuario_id, 'accion': accion, 'referencia': str(registro_id)})
