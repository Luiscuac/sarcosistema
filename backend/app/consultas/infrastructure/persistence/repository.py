"""Consultas parametrizadas sobre el esquema clínico existente."""
import json

from sqlalchemy import text

from app.consultas.domain.entities import CLINICOS, MedicoVigente


PACIENTE_CAMPOS = '''p.id, p.codigo_paciente, p.historia_clinica, p.codigo_externo,
    p.nombre_completo, p.tipo_documento, p.numero_documento, p.fecha_nacimiento,
    p.sexo, p.estado'''
FILTRO_BUSQUEDA = '''p.estado = 'activo' AND (
    strpos(lower(p.nombre_completo), lower(:buscar)) > 0 OR
    strpos(lower(coalesce(p.numero_documento, '')), lower(:buscar)) > 0 OR
    strpos(lower(p.codigo_paciente), lower(:buscar)) > 0 OR
    strpos(lower(coalesce(p.historia_clinica, '')), lower(:buscar)) > 0 OR
    strpos(lower(coalesce(p.codigo_externo, '')), lower(:buscar)) > 0)'''
CONSULTA_CAMPOS = '''c.id, c.paciente_id, c.medico_id, c.especialidad_id,
    c.fecha_hora_inicio, c.fecha_hora_fin, c.motivo_consulta, c.estado,
    c.datos_clinicos_jsonb, t.nombre_completo AS medico_nombre,
    p.nombre_completo AS paciente_nombre, p.estado AS paciente_estado,
    p.codigo_paciente AS paciente_codigo, p.historia_clinica AS paciente_historia,
    p.numero_documento AS paciente_documento, p.fecha_nacimiento AS paciente_nacimiento,
    p.sexo AS paciente_sexo'''


def presentar_consulta(row):
    if row is None:
        return None
    resultado = dict(row)
    clinicos = resultado.pop('datos_clinicos_jsonb', None) or {}
    if 'paciente_nombre' in resultado:
        resultado['paciente'] = {
            'id': resultado['paciente_id'],
            'nombre_completo': resultado.pop('paciente_nombre'),
            'estado': resultado.pop('paciente_estado', None),
            'codigo_paciente': resultado.pop('paciente_codigo', None),
            'historia_clinica': resultado.pop('paciente_historia', None),
            'numero_documento': resultado.pop('paciente_documento', None),
            'fecha_nacimiento': resultado.pop('paciente_nacimiento', None),
            'sexo': resultado.pop('paciente_sexo', None),
        }
    if isinstance(clinicos, str):
        clinicos = json.loads(clinicos)
    resultado['diagnostico_principal'] = None
    resultado.update({campo: valor for campo, valor in clinicos.items() if campo in CLINICOS})
    return resultado


class SqlAlchemyConsultaRepository:
    def __init__(self, db):
        self.db = db

    async def buscar_pacientes(self, buscar: str, pagina: int, limite: int):
        parametros = {'buscar': buscar, 'limite': limite, 'offset': (pagina - 1) * limite}
        total = (await self.db.execute(text(f'SELECT count(*) FROM public.paciente p WHERE {FILTRO_BUSQUEDA}'), parametros)).scalar_one()
        filas = (await self.db.execute(text(f'''
            SELECT {PACIENTE_CAMPOS} FROM public.paciente p WHERE {FILTRO_BUSQUEDA}
            ORDER BY p.nombre_completo, p.id LIMIT :limite OFFSET :offset
        '''), parametros)).mappings().all()
        return {'items': [dict(fila) for fila in filas], 'total': total, 'pagina': pagina, 'limite': limite}

    async def obtener_paciente(self, id: int):
        fila = (await self.db.execute(text(f'''
            SELECT {PACIENTE_CAMPOS} FROM public.paciente p
            WHERE p.id = :id AND p.estado = 'activo'
        '''), {'id': id})).mappings().one_or_none()
        return dict(fila) if fila else None

    async def listar_historial(self, paciente_id: int, pagina: int, limite: int):
        params = {'id': paciente_id, 'limite': limite, 'offset': (pagina - 1) * limite}
        total = (await self.db.execute(text('SELECT count(*) FROM public.consulta WHERE paciente_id = :id'), params)).scalar_one()
        filas = (await self.db.execute(text(f'''
            SELECT {CONSULTA_CAMPOS} FROM public.consulta c
            JOIN public.medico m ON m.id = c.medico_id
            JOIN public.trabajador t ON t.id = m.trabajador_id
            JOIN public.paciente p ON p.id = c.paciente_id
            WHERE c.paciente_id = :id
            ORDER BY c.fecha_hora_inicio DESC, c.id DESC
            LIMIT :limite OFFSET :offset
        '''), params)).mappings().all()
        return {'items': [presentar_consulta(fila) for fila in filas], 'total': total,
                'pagina': pagina, 'limite': limite}

    async def obtener_consulta(self, id: int):
        fila = (await self.db.execute(text(f'''
            SELECT {CONSULTA_CAMPOS} FROM public.consulta c
            JOIN public.medico m ON m.id = c.medico_id
            JOIN public.trabajador t ON t.id = m.trabajador_id
            JOIN public.paciente p ON p.id = c.paciente_id
            WHERE c.id = :id
        '''), {'id': id})).mappings().one_or_none()
        return presentar_consulta(fila)

    async def medico_vigente(self, usuario_id: int) -> MedicoVigente | None:
        filas = (await self.db.execute(text('''
            SELECT m.id, me.especialidad_id FROM public.usuario u
            JOIN public.trabajador t ON t.id = u.trabajador_id
            JOIN public.medico m ON m.trabajador_id = t.id
            JOIN public.medico_especialidad me ON me.medico_id = m.id
            JOIN public.especialidad e ON e.id = me.especialidad_id
            WHERE u.id = :id AND u.estado = 'activo' AND t.estado = 'activo'
                AND m.activo AND me.vigente AND e.activo
        '''), {'id': usuario_id})).mappings().all()
        return MedicoVigente(**filas[0]) if len(filas) == 1 else None

    async def crear(self, datos, usuario_id: int, medico: MedicoVigente):
        clinicos = datos.contenido()
        params = {
            'paciente': datos.paciente_id, 'medico': medico.id,
            'especialidad': medico.especialidad_id, 'motivo': datos.motivo_consulta,
            'json': json.dumps(clinicos, ensure_ascii=False, allow_nan=False),
            'usuario': usuario_id, 'clave': datos.clave_idempotencia,
        }
        repetida = await self._repeticion(datos, medico, clinicos, params)
        if repetida is not None:
            return repetida, False
        paciente = await self.obtener_paciente(datos.paciente_id)
        if paciente is None:
            raise LookupError('Paciente no encontrado.')
        insertado = (await self.db.execute(text('''
            INSERT INTO public.consulta (paciente_id, medico_id, especialidad_id,
                fecha_hora_inicio, fecha_hora_fin, motivo_consulta, estado,
                datos_clinicos_jsonb, clave_idempotencia, usuario_creacion_id, created_by)
            VALUES (:paciente, :medico, :especialidad, now(), now(), :motivo,
                'cerrada', CAST(:json AS jsonb), :clave, :usuario, :usuario)
            ON CONFLICT (usuario_creacion_id, clave_idempotencia) DO NOTHING
            RETURNING id
        '''), params)).scalar_one_or_none()
        if insertado is None:
            return await self._repeticion(datos, medico, clinicos, params), False

        await self.db.execute(text('''
            INSERT INTO public.auditoria_accion (fecha_hora, usuario_id, accion,
                entidad_afectada, referencia_registro)
            VALUES (now(), :usuario, 'crear', 'consulta', :referencia)
        '''), {'usuario': usuario_id, 'referencia': str(insertado)})
        return await self.obtener_consulta(insertado), True

    async def _repeticion(self, datos, medico, clinicos, params):
        existente = (await self.db.execute(text('''
            SELECT id, paciente_id, medico_id, especialidad_id, motivo_consulta,
                datos_clinicos_jsonb FROM public.consulta
            WHERE usuario_creacion_id = :usuario AND clave_idempotencia = :clave
        '''), params)).mappings().one_or_none()
        if existente is None:
            return None
        if (existente['paciente_id'] != datos.paciente_id
                or existente['medico_id'] != medico.id
                or existente['especialidad_id'] != medico.especialidad_id
                or existente['motivo_consulta'] != datos.motivo_consulta
                or existente['datos_clinicos_jsonb'] != clinicos):
            raise FileExistsError('La clave de envío ya se usó para otra consulta.')
        return await self.obtener_consulta(existente['id'])
