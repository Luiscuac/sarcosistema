"""Persistencia de radiologia convencional: catalogo, solicitudes, adquisicion, imagenes e informes.

Reutiliza las tablas clinicas compartidas (solicitud, estudio_solicitado, informe_imagen,
archivo_imagen) y agrega las tablas `radiologia_*`. No hace commit: la transaccion la
administra `get_db`.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.imagenes.domain import radiologia as reglas
from app.imagenes.domain.catalogo_radiologia import CATEGORIAS
from app.imagenes.domain.errors import EstudioNoEncontrado


class ConflictoRadiologia(Exception):
    """La operacion no corresponde al estado actual del estudio o del informe."""

    def __init__(self, mensaje: str, pendientes: list[str] | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.pendientes = pendientes or []


ESTADOS_ABIERTOS = ('pendiente_muestra', 'resultado_en_preparacion')
ESTADOS_CERRADOS = ('publicado', 'no_realizado', 'invalidado')
DESCRIPCION_ESTADO = {
    'pendiente_muestra': 'Solicitud registrada',
    'resultado_en_preparacion': 'Adquisición completada: pendiente de informe',
    'publicado': 'Informe validado',
    'no_realizado': 'Estudio marcado como no realizado',
    'invalidado': 'Estudio anulado',
}

_FILAS = '''
SELECT e.id AS estudio_id, e.referencia AS referencia_estudio, s.id AS solicitud_id, s.referencia AS referencia_solicitud,
       p.id AS paciente_id, p.nombre_completo AS paciente_nombre, p.numero_documento AS paciente_documento,
       t.codigo AS tipo_estudio_codigo, t.nombre AS tipo_estudio_nombre,
       t.configuracion_radiologia->>'categoria' AS categoria,
       d.lateralidad, s.prioridad, e.estado, s.fecha_solicitud,
       COALESCE(s.medico_solicitante_nombre_snapshot, tm.nombre_completo) AS medico_solicitante,
       (a.estudio_id IS NOT NULL) AS tiene_adquisicion,
       (d.entregado_en IS NOT NULL) AS entregado,
       COALESCE(inf.con_contenido, false) AS informe_con_contenido,
       COALESCE(inf.imagenes, 0) AS imagenes
  FROM public.estudio_solicitado e
  JOIN public.solicitud s ON s.id = e.solicitud_id
  JOIN public.paciente p ON p.id = e.paciente_id
  JOIN public.tipo_estudio t ON t.id = e.tipo_estudio_id
  JOIN public.servicio v ON v.id = e.servicio_id AND v.codigo = 'IMG'
  LEFT JOIN public.radiologia_estudio_detalle d ON d.estudio_id = e.id
  LEFT JOIN public.radiologia_adquisicion a ON a.estudio_id = e.id
  LEFT JOIN public.medico m ON m.id = s.medico_solicitante_id
  LEFT JOIN public.trabajador tm ON tm.id = m.trabajador_id
  LEFT JOIN LATERAL (
      SELECT (COALESCE(btrim(i.descripcion_texto), '') <> '') AS con_contenido,
             (SELECT count(*) FROM public.archivo_imagen ai
               WHERE ai.informe_id = i.id AND ai.activo
                 AND (ai.mime_type LIKE 'image/%' OR ai.mime_type = 'application/dicom')) AS imagenes
        FROM public.informe_imagen i
       WHERE i.estudio_id = e.id
       ORDER BY i.numero_version DESC LIMIT 1
  ) inf ON true
 WHERE t.codigo LIKE 'RX\\_%'
'''


def _json(valor) -> str:
    return json.dumps(valor, ensure_ascii=False)


def _edad(nacimiento: date | None) -> int | None:
    if nacimiento is None:
        return None
    hoy = date.today()
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


def _fila(fila) -> dict:
    datos = dict(fila)
    etapa = reglas.etapa_estudio(datos['estado'], datos.pop('tiene_adquisicion'),
                                 datos.pop('informe_con_contenido'), datos.pop('entregado'))
    return datos | {'etapa': etapa, 'etapa_texto': reglas.ETAPAS[etapa], 'triaje': None}


class RepositorioRadiologiaSql:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _todos(self, sql: str, **parametros) -> list[dict]:
        return [dict(f) for f in (await self.db.execute(text(sql), parametros)).mappings().all()]

    async def _uno(self, sql: str, **parametros) -> dict | None:
        fila = (await self.db.execute(text(sql), parametros)).mappings().first()
        return dict(fila) if fila else None

    async def _auditar(self, usuario_id: int, accion: str, estudio_id: int, descripcion: str, **detalle) -> None:
        await self.db.execute(text('''INSERT INTO public.auditoria_accion
            (fecha_hora, usuario_id, accion, entidad_afectada, referencia_registro, detalle)
            VALUES (now(), :u, :a, 'radiologia_estudio', :r, CAST(:d AS jsonb))'''),
            {'u': usuario_id, 'a': accion, 'r': str(estudio_id), 'd': _json({'descripcion': descripcion, **detalle})})

    # ---------- catalogo ----------

    async def catalogo(self, incluir_inactivos: bool = False) -> dict:
        estudios = await self._todos('''
            SELECT t.id, t.codigo, t.nombre, t.activo, t.configuracion_radiologia AS config
              FROM public.tipo_estudio t JOIN public.servicio v ON v.id = t.servicio_id AND v.codigo = 'IMG' AND v.activo
             WHERE t.configuracion_radiologia IS NOT NULL AND t.codigo LIKE 'RX\\_%' AND (t.activo OR :todos)
             ORDER BY t.nombre''', todos=incluir_inactivos)
        usadas = {e['config'].get('categoria') for e in estudios}
        return {'categorias': [{'codigo': c, 'nombre': n} for c, n in CATEGORIAS.items() if c in usadas], 'estudios': estudios}

    async def cambiar_activo(self, tipo_estudio_id: int, activo: bool, usuario_id: int) -> dict | None:
        fila = await self._uno('''UPDATE public.tipo_estudio t SET activo = :activo
              FROM public.servicio v
             WHERE v.id = t.servicio_id AND v.codigo = 'IMG' AND t.id = :id
               AND t.configuracion_radiologia IS NOT NULL AND t.codigo LIKE 'RX\\_%'
            RETURNING t.id, t.codigo, t.nombre, t.activo, t.configuracion_radiologia AS config''', id=tipo_estudio_id, activo=activo)
        if fila:
            await self.db.execute(text('''INSERT INTO public.auditoria_accion
                (fecha_hora, usuario_id, accion, entidad_afectada, referencia_registro, detalle)
                VALUES (now(), :u, 'modificar', 'tipo_estudio', :r, CAST(:d AS jsonb))'''),
                {'u': usuario_id, 'r': str(tipo_estudio_id), 'd': _json({'activo': activo})})
        return fila

    # ---------- solicitudes ----------

    async def crear_solicitud(self, datos: dict, usuario_id: int, rol: str) -> dict:
        clave = datos['clave_idempotencia']
        existente = await self._uno('SELECT id, referencia, created_by FROM public.solicitud WHERE clave_idempotencia = :c', c=clave)
        if existente:
            if existente['created_by'] != usuario_id:
                raise reglas.ReglaRadiologia('La clave de envío ya se usó en otra solicitud')
            return await self._solicitud_creada(existente['id'], existente['referencia'])

        paciente = await self._uno("SELECT id FROM public.paciente WHERE id = :p AND estado = 'activo'", p=datos['paciente_id'])
        if paciente is None:
            raise reglas.ReglaRadiologia('El paciente no existe o está inactivo')

        ids = list({item['tipo_estudio_id'] for item in datos['estudios']})
        tipos = {t['id']: t for t in await self._todos('''
            SELECT t.id, t.nombre, t.servicio_id, t.configuracion_radiologia AS config
              FROM public.tipo_estudio t JOIN public.servicio v ON v.id = t.servicio_id AND v.codigo = 'IMG' AND v.activo
             WHERE t.id = ANY(:ids) AND t.activo AND t.configuracion_radiologia IS NOT NULL AND t.codigo LIKE 'RX\\_%' ''', ids=ids)}
        if len(tipos) != len(ids):
            raise reglas.ReglaRadiologia('Uno o más estudios no están habilitados en el catálogo de Rayos X')

        detalles, vistos = [], set()
        for item in datos['estudios']:
            tipo = tipos[item['tipo_estudio_id']]
            try:
                detalle = reglas.normalizar_detalle_solicitud(tipo['config'], item)
            except reglas.ReglaRadiologia as error:
                raise reglas.ReglaRadiologia(f'{tipo["nombre"]}: {error}') from None
            firma = (tipo['id'], detalle['lateralidad'])
            if firma in vistos:
                raise reglas.ReglaRadiologia(f'{tipo["nombre"]}: está repetido en la solicitud')
            vistos.add(firma)
            detalles.append((tipo, detalle))

        medico_id, medico_nombre, establecimiento, procedencia = await self._solicitante(datos, usuario_id, rol)
        referencia = f'RX-{datetime.now(timezone.utc):%y%m%d}-{uuid4().hex[:6].upper()}'
        solicitud_id = (await self.db.execute(text('''INSERT INTO public.solicitud
            (referencia, paciente_id, fecha_solicitud, procedencia, establecimiento_solicitante_nombre_snapshot,
             medico_solicitante_id, medico_solicitante_nombre_snapshot, diagnostico_principal, prioridad,
             clave_idempotencia, created_by)
            VALUES (:ref, :p, now(), :proc, :est, :mid, :mnom, :dx, :pri, :clave, :u) RETURNING id'''),
            {'ref': referencia, 'p': datos['paciente_id'], 'proc': procedencia, 'est': establecimiento, 'mid': medico_id,
             'mnom': medico_nombre, 'dx': datos.get('diagnostico_principal'), 'pri': datos['prioridad'],
             'clave': clave, 'u': usuario_id})).scalar_one()
        for tipo, detalle in detalles:
            estudio_id = (await self.db.execute(text('''INSERT INTO public.estudio_solicitado
                (referencia, solicitud_id, paciente_id, servicio_id, tipo_estudio_id, estado, created_by)
                VALUES (:ref, :s, :p, :v, :t, 'pendiente_muestra', :u) RETURNING id'''),
                {'ref': f'{referencia}-{uuid4().hex[:4].upper()}', 's': solicitud_id, 'p': datos['paciente_id'],
                 'v': tipo['servicio_id'], 't': tipo['id'], 'u': usuario_id})).scalar_one()
            await self.db.execute(text('''INSERT INTO public.radiologia_estudio_detalle
                (estudio_id, lateralidad, protocolo_codigo, proyecciones_solicitadas, indicacion_clinica, observaciones,
                 detalle_region, created_by)
                VALUES (:e, :lat, :prot, CAST(:proy AS jsonb), :ind, :obs, :det, :u)'''),
                {'e': estudio_id, 'lat': detalle['lateralidad'], 'prot': detalle['protocolo_codigo'],
                 'proy': _json(detalle['proyecciones_solicitadas']), 'ind': detalle['indicacion_clinica'],
                 'obs': detalle['observaciones'], 'det': detalle['detalle_region'], 'u': usuario_id})
        await self.db.execute(text('''INSERT INTO public.auditoria_accion
            (fecha_hora, usuario_id, accion, entidad_afectada, referencia_registro, detalle)
            VALUES (now(), :u, 'crear', 'solicitud', :r, CAST(:d AS jsonb))'''),
            {'u': usuario_id, 'r': str(solicitud_id), 'd': _json({'origen': 'rayos_x', 'estudios': len(detalles)})})
        return await self._solicitud_creada(solicitud_id, referencia)

    async def _solicitud_creada(self, solicitud_id: int, referencia: str) -> dict:
        estudios = await self._todos('SELECT id AS estudio_id, referencia FROM public.estudio_solicitado WHERE solicitud_id = :s ORDER BY id', s=solicitud_id)
        return {'solicitud_id': solicitud_id, 'referencia': referencia, 'estudios': estudios}

    async def _solicitante(self, datos: dict, usuario_id: int, rol: str):
        medicos_activos = '''SELECT m.id, t.nombre_completo AS nombre FROM public.medico m
            JOIN public.trabajador t ON t.id = m.trabajador_id JOIN public.usuario u ON u.trabajador_id = t.id
            JOIN public.rol r ON r.id = u.rol_id
            WHERE m.activo AND t.estado = 'activo' AND u.estado = 'activo' AND r.activo AND r.codigo = 'medico' '''
        if rol == 'medico':
            medico = await self._uno(medicos_activos + ' AND u.id = :u', u=usuario_id)
            if medico is None:
                raise reglas.ReglaRadiologia('Tu usuario no está vinculado a un médico activo')
            return medico['id'], medico['nombre'], None, 'este_centro'
        if datos.get('procedencia', 'este_centro') == 'este_centro':
            medico = await self._uno(medicos_activos + ' AND m.id = :m', m=datos.get('medico_solicitante_id') or 0)
            if medico is None:
                raise reglas.ReglaRadiologia('Selecciona un médico solicitante activo de este centro')
            return medico['id'], medico['nombre'], None, 'este_centro'
        nombre = (datos.get('medico_solicitante_nombre') or '').strip()
        establecimiento = (datos.get('establecimiento_solicitante_nombre') or '').strip()
        if len(nombre) < 2 or len(establecimiento) < 2:
            raise reglas.ReglaRadiologia('Indica el establecimiento y el médico solicitante externos')
        return None, nombre, establecimiento, 'otro_centro'

    # ---------- listados ----------

    async def listar_estudios(self, vista: str | None = None, paciente_id: int | None = None,
                              solicitud_id: int | None = None) -> list[dict]:
        filtros, parametros = '', {}
        if vista == 'activos':
            filtros += ' AND e.estado = ANY(:estados)'
            parametros['estados'] = list(ESTADOS_ABIERTOS)
        elif vista == 'finalizados':
            filtros += ' AND e.estado = ANY(:estados)'
            parametros['estados'] = list(ESTADOS_CERRADOS)
        if paciente_id is not None:
            filtros += ' AND e.paciente_id = :paciente'
            parametros['paciente'] = paciente_id
        if solicitud_id is not None:
            filtros += ' AND e.solicitud_id = :solicitud'
            parametros['solicitud'] = solicitud_id
        orden = ' ORDER BY s.fecha_solicitud DESC, e.id DESC LIMIT 500' if vista != 'activos' else " ORDER BY (s.prioridad = 'urgente') DESC, s.fecha_solicitud, e.id LIMIT 500"
        return [_fila(f) for f in await self._todos(_FILAS + filtros + orden, **parametros)]

    async def paciente(self, paciente_id: int) -> dict | None:
        fila = await self._uno('''SELECT id, nombre_completo, numero_documento, codigo_paciente, fecha_nacimiento, sexo
            FROM public.paciente WHERE id = :p''', p=paciente_id)
        return fila | {'edad': _edad(fila['fecha_nacimiento'])} if fila else None

    async def solicitud(self, solicitud_id: int) -> dict | None:
        return await self._uno('''SELECT s.id, s.referencia, s.fecha_solicitud, s.prioridad, s.procedencia, s.paciente_id,
                   COALESCE(s.medico_solicitante_nombre_snapshot, tm.nombre_completo) AS medico_solicitante,
                   s.establecimiento_solicitante_nombre_snapshot AS establecimiento, s.diagnostico_principal
              FROM public.solicitud s
              LEFT JOIN public.medico m ON m.id = s.medico_solicitante_id
              LEFT JOIN public.trabajador tm ON tm.id = m.trabajador_id
             WHERE s.id = :s AND EXISTS (SELECT 1 FROM public.estudio_solicitado e
                   JOIN public.tipo_estudio t ON t.id = e.tipo_estudio_id
                  WHERE e.solicitud_id = s.id AND t.codigo LIKE 'RX\\_%')''', s=solicitud_id)

    # ---------- detalle ----------

    async def base(self, estudio_id: int) -> dict:
        """Fila del estudio con su configuracion; EstudioNoEncontrado si no es de Rayos X."""
        filas = await self._todos(_FILAS + ' AND e.id = :id', id=estudio_id)
        if not filas:
            raise EstudioNoEncontrado(f'El estudio {estudio_id} no existe')
        config = (await self.db.execute(text('''SELECT t.configuracion_radiologia FROM public.estudio_solicitado e
            JOIN public.tipo_estudio t ON t.id = e.tipo_estudio_id WHERE e.id = :id'''), {'id': estudio_id})).scalar_one()
        return {'fila': _fila(filas[0]), 'config': config or _config_generica(filas[0]['tipo_estudio_nombre'])}

    async def _informe_actual(self, estudio_id: int) -> dict | None:
        return await self._uno('''SELECT i.id, i.numero_version, i.estado, i.descripcion_texto AS texto, i.fecha_hora_publicacion,
                   (r.informe_id IS NOT NULL) AS estructurado, r.plantilla_codigo, COALESCE(r.contenido, '{}'::jsonb) AS contenido,
                   COALESCE(r.texto_personalizado, false) AS texto_personalizado, COALESCE(r.version_edicion, 0) AS version_edicion,
                   r.responsable_nombre, r.registro_profesional
              FROM public.informe_imagen i LEFT JOIN public.radiologia_informe r ON r.informe_id = i.id
             WHERE i.estudio_id = :e ORDER BY i.numero_version DESC LIMIT 1''', e=estudio_id)

    async def imagenes(self, estudio_id: int) -> list[dict]:
        return await self._todos('''SELECT ai.id, ai.id AS archivo_id, ai.nombre_original, ai.mime_type, ai.tamano_bytes,
                   ai.hash_sha256, ai.fecha_carga, ri.proyeccion_codigo
              FROM public.archivo_imagen ai
              JOIN public.informe_imagen i ON i.id = ai.informe_id
              LEFT JOIN public.radiologia_imagen ri ON ri.archivo_imagen_id = ai.id
             WHERE i.id = (SELECT id FROM public.informe_imagen WHERE estudio_id = :e ORDER BY numero_version DESC LIMIT 1)
               AND ai.activo AND (ai.mime_type LIKE 'image/%' OR ai.mime_type = 'application/dicom')
             ORDER BY ai.id''', e=estudio_id)

    async def adquisicion(self, estudio_id: int) -> dict | None:
        return await self._uno('''SELECT estado, proyecciones_realizadas, lateralidad_realizada, posicion_paciente,
                   fecha_hora_adquisicion, operador_nombre, calidad, limitaciones, repeticiones, motivo_repeticion,
                   parametros, observaciones, completada_en
              FROM public.radiologia_adquisicion WHERE estudio_id = :e''', e=estudio_id)

    async def informes_externos(self, estudio_id: int) -> list[dict]:
        return await self._todos('''SELECT id, nombre_original, mime_type, tamano_bytes, establecimiento, profesional,
                   fecha_informe, observaciones, fecha_carga
              FROM public.radiologia_informe_externo WHERE estudio_id = :e AND activo ORDER BY id''', e=estudio_id)

    async def detalle(self, estudio_id: int) -> dict:
        base = await self.base(estudio_id)
        fila, config = base['fila'], base['config']
        detalle = await self._uno('''SELECT lateralidad, protocolo_codigo, proyecciones_solicitadas, indicacion_clinica,
                   observaciones, detalle_region, motivo_no_realizado, entregado_en, entregado_a
              FROM public.radiologia_estudio_detalle WHERE estudio_id = :e''', e=estudio_id) or {
            'lateralidad': None, 'protocolo_codigo': None, 'proyecciones_solicitadas': [], 'indicacion_clinica': None,
            'observaciones': None, 'detalle_region': None, 'motivo_no_realizado': None, 'entregado_en': None, 'entregado_a': None}
        informe = await self._informe_actual(estudio_id)
        # El borrador tecnico creado al subir imagenes no es todavia un informe.
        if informe and informe['estado'] == 'borrador' and not informe['estructurado'] and not (informe['texto'] or '').strip():
            informe = None
        adquisicion = await self.adquisicion(estudio_id)
        imagenes = await self.imagenes(estudio_id)
        externos = await self.informes_externos(estudio_id)
        adendas = await self._todos('''SELECT ad.id, ad.motivo, ad.texto, ad.autor_nombre, ad.registro_profesional, ad.fecha_hora
              FROM public.radiologia_adenda ad JOIN public.informe_imagen i ON i.id = ad.informe_id
             WHERE i.estudio_id = :e ORDER BY ad.id''', e=estudio_id)
        historial = await self._todos('''
            SELECT h.fecha_hora, 'estado' AS tipo, h.estado_nuevo AS clave, NULL AS descripcion, u.identificador_acceso AS usuario
              FROM public.estudio_estado_historial h LEFT JOIN public.usuario u ON u.id = h.usuario_id
             WHERE h.estudio_id = :e
            UNION ALL
            SELECT au.fecha_hora, 'accion', au.accion, au.detalle->>'descripcion', u.identificador_acceso
              FROM public.auditoria_accion au LEFT JOIN public.usuario u ON u.id = au.usuario_id
             WHERE au.entidad_afectada = 'radiologia_estudio' AND au.referencia_registro = :r
             ORDER BY 1, 2 DESC''', e=estudio_id, r=str(estudio_id))
        for evento in historial:
            clave = evento.pop('clave')
            if evento['tipo'] == 'estado':
                evento['descripcion'] = DESCRIPCION_ESTADO.get(clave, clave)
        return {
            'estudio': fila | {'detalle': detalle},
            'paciente': await self.paciente(fila['paciente_id']),
            'solicitud': {k: v for k, v in (await self.solicitud(fila['solicitud_id']) or {}).items() if k != 'paciente_id'},
            'config': config,
            'adquisicion': adquisicion,
            'imagenes': imagenes,
            'informe': informe,
            'adendas': adendas,
            'informes_externos': externos,
            'historial': historial,
            'pendientes': {
                'adquisicion': [] if fila['estado'] != 'pendiente_muestra'
                else reglas.pendientes_para_completar_adquisicion(config, adquisicion, len(imagenes)),
                'validacion': [] if fila['estado'] != 'resultado_en_preparacion'
                else reglas.pendientes_para_validar((informe or {}).get('contenido'), (informe or {}).get('texto'), len(imagenes), bool(externos)),
            },
        }

    async def _abierto(self, estudio_id: int, estados=ESTADOS_ABIERTOS) -> dict:
        base = await self.base(estudio_id)
        if base['fila']['estado'] not in estados:
            raise ConflictoRadiologia('El estudio ya no admite esta operación en su estado actual.')
        return base

    async def _cambiar_estado(self, estudio_id: int, estado: str, usuario_id: int) -> None:
        await self.db.execute(text('''UPDATE public.estudio_solicitado SET estado = :estado, updated_by = :u, updated_at = now()
            WHERE id = :e'''), {'estado': estado, 'u': usuario_id, 'e': estudio_id})

    # ---------- adquisicion e imagenes ----------

    async def guardar_adquisicion(self, estudio_id: int, datos: dict, usuario_id: int) -> None:
        base = await self._abierto(estudio_id)
        limpio = reglas.normalizar_adquisicion(base['config'], datos)
        await self.db.execute(text('''INSERT INTO public.radiologia_adquisicion
            (estudio_id, proyecciones_realizadas, lateralidad_realizada, posicion_paciente, fecha_hora_adquisicion,
             operador_usuario_id, operador_nombre, calidad, limitaciones, repeticiones, motivo_repeticion, parametros,
             observaciones, updated_by)
            VALUES (:e, CAST(:proy AS jsonb), :lat, :pos, :fecha, :u, :op, :cal, :lim, :rep, :mot, CAST(:par AS jsonb), :obs, :u)
            ON CONFLICT (estudio_id) DO UPDATE SET
                proyecciones_realizadas = EXCLUDED.proyecciones_realizadas, lateralidad_realizada = EXCLUDED.lateralidad_realizada,
                posicion_paciente = EXCLUDED.posicion_paciente, fecha_hora_adquisicion = EXCLUDED.fecha_hora_adquisicion,
                operador_nombre = EXCLUDED.operador_nombre, calidad = EXCLUDED.calidad, limitaciones = EXCLUDED.limitaciones,
                repeticiones = EXCLUDED.repeticiones, motivo_repeticion = EXCLUDED.motivo_repeticion,
                parametros = EXCLUDED.parametros, observaciones = EXCLUDED.observaciones,
                updated_by = EXCLUDED.updated_by, updated_at = now()'''),
            {'e': estudio_id, 'proy': _json(limpio['proyecciones_realizadas']), 'lat': limpio['lateralidad_realizada'],
             'pos': limpio['posicion_paciente'], 'fecha': datos.get('fecha_hora_adquisicion'), 'u': usuario_id,
             'op': limpio['operador_nombre'], 'cal': limpio['calidad'], 'lim': limpio['limitaciones'],
             'rep': limpio['repeticiones'], 'mot': limpio['motivo_repeticion'], 'par': _json(limpio['parametros']),
             'obs': limpio['observaciones']})
        await self._auditar(usuario_id, 'modificar', estudio_id, 'Registro técnico de adquisición guardado')

    async def completar_adquisicion(self, estudio_id: int, usuario_id: int) -> None:
        base = await self._abierto(estudio_id, ('pendiente_muestra',))
        faltan = reglas.pendientes_para_completar_adquisicion(
            base['config'], await self.adquisicion(estudio_id), len(await self.imagenes(estudio_id)))
        if faltan:
            raise ConflictoRadiologia('Faltan datos para completar la adquisición.', faltan)
        await self.db.execute(text('''UPDATE public.radiologia_adquisicion SET estado = 'completada', completada_en = now(),
            updated_by = :u, updated_at = now() WHERE estudio_id = :e'''), {'u': usuario_id, 'e': estudio_id})
        await self._cambiar_estado(estudio_id, 'resultado_en_preparacion', usuario_id)

    async def _informe_de_trabajo(self, estudio_id: int, usuario_id: int) -> int:
        """Informe en borrador al que se asocian imagenes y contenido; se crea vacio si no existe."""
        informe = await self._uno('''SELECT id, estado FROM public.informe_imagen WHERE estudio_id = :e
            ORDER BY numero_version DESC LIMIT 1''', e=estudio_id)
        if informe is None:
            return (await self.db.execute(text('''INSERT INTO public.informe_imagen (estudio_id, numero_version, estado, created_by)
                VALUES (:e, 1, 'borrador', :u) RETURNING id'''), {'e': estudio_id, 'u': usuario_id})).scalar_one()
        if informe['estado'] != 'borrador':
            raise ConflictoRadiologia('El informe ya está validado: no admite cambios.')
        return informe['id']

    async def agregar_imagenes(self, estudio_id: int, archivos: list[dict], usuario_id: int) -> list[dict]:
        """archivos: metadatos ya guardados en disco + 'proyeccion_codigo'. Devuelve las filas creadas."""
        base = await self._abierto(estudio_id)
        permitidas = {p['codigo'] for p in base['config'].get('proyecciones', [])}
        informe_id = await self._informe_de_trabajo(estudio_id, usuario_id)
        existentes = {i['hash_sha256'] for i in await self.imagenes(estudio_id)}
        creadas = []
        for archivo in archivos:
            proyeccion = archivo.get('proyeccion_codigo') or None
            if proyeccion is not None and proyeccion not in permitidas:
                raise reglas.ReglaRadiologia(f'La proyección {proyeccion} no corresponde a este estudio')
            if archivo['hash_sha256'] in existentes:
                raise reglas.ReglaRadiologia(f'{archivo["nombre_original"]}: esta imagen ya está adjunta al estudio')
            existentes.add(archivo['hash_sha256'])
            fila = await self._uno('''INSERT INTO public.archivo_imagen
                (informe_id, nombre_original, url_archivo, mime_type, tamano_bytes, hash_sha256, fecha_carga, activo, created_by)
                VALUES (:i, :n, :url, :m, :t, :h, now(), true, :u)
                RETURNING id, mime_type, hash_sha256''', i=informe_id, n=archivo['nombre_original'], url=archivo['url_archivo'],
                m=archivo['mime_type'], t=archivo['tamano_bytes'], h=archivo['hash_sha256'], u=usuario_id)
            await self.db.execute(text('''INSERT INTO public.radiologia_imagen (estudio_id, archivo_imagen_id, proyeccion_codigo)
                VALUES (:e, :a, :p)'''), {'e': estudio_id, 'a': fila['id'], 'p': proyeccion})
            creadas.append(fila)
        await self._auditar(usuario_id, 'crear', estudio_id, f'{len(creadas)} imagen(es) adjuntada(s)', archivos=len(creadas))
        return creadas

    async def _imagen_del_estudio(self, estudio_id: int, imagen_id: int) -> dict:
        imagen = next((i for i in await self.imagenes(estudio_id) if i['id'] == imagen_id), None)
        if imagen is None:
            raise EstudioNoEncontrado('La imagen no pertenece a este estudio')
        return imagen

    async def asignar_proyeccion(self, estudio_id: int, imagen_id: int, proyeccion: str | None, usuario_id: int) -> None:
        base = await self._abierto(estudio_id)
        await self._imagen_del_estudio(estudio_id, imagen_id)
        if proyeccion is not None and proyeccion not in {p['codigo'] for p in base['config'].get('proyecciones', [])}:
            raise reglas.ReglaRadiologia('La proyección no corresponde a este estudio')
        await self.db.execute(text('''INSERT INTO public.radiologia_imagen (estudio_id, archivo_imagen_id, proyeccion_codigo)
            VALUES (:e, :a, :p) ON CONFLICT (archivo_imagen_id) DO UPDATE SET proyeccion_codigo = EXCLUDED.proyeccion_codigo'''),
            {'e': estudio_id, 'a': imagen_id, 'p': proyeccion})
        await self._auditar(usuario_id, 'modificar', estudio_id, 'Proyección de una imagen actualizada', archivo=imagen_id)

    async def retirar_imagen(self, estudio_id: int, imagen_id: int, motivo: str, usuario_id: int) -> None:
        await self._abierto(estudio_id)
        imagen = await self._imagen_del_estudio(estudio_id, imagen_id)
        await self.db.execute(text('UPDATE public.archivo_imagen SET activo = false, motivo_retiro = :m WHERE id = :a'),
                              {'m': motivo, 'a': imagen_id})
        await self._auditar(usuario_id, 'anular', estudio_id, f'Imagen retirada ({imagen["nombre_original"]}): {motivo}', archivo=imagen_id)

    async def marcar_no_realizado(self, estudio_id: int, motivo: str, usuario_id: int) -> None:
        base = await self._abierto(estudio_id)
        if base['fila']['etapa'] == 'borrador':
            raise ConflictoRadiologia('El estudio ya tiene un informe en borrador.')
        await self.db.execute(text('''INSERT INTO public.radiologia_estudio_detalle (estudio_id, motivo_no_realizado, created_by)
            VALUES (:e, :m, :u) ON CONFLICT (estudio_id) DO UPDATE SET motivo_no_realizado = EXCLUDED.motivo_no_realizado'''),
            {'e': estudio_id, 'm': motivo, 'u': usuario_id})
        await self._cambiar_estado(estudio_id, 'no_realizado', usuario_id)
        await self._auditar(usuario_id, 'anular', estudio_id, f'No realizado: {motivo}')

    # ---------- informe ----------

    async def guardar_borrador(self, estudio_id: int, contenido: dict, texto_final: str | None,
                               version_edicion: int | None, usuario_id: int) -> None:
        base = await self._abierto(estudio_id, ('resultado_en_preparacion',))
        config = base['config']
        limpio = reglas.normalizar_contenido(config, contenido)
        texto_final = reglas.normalizar_texto_final(texto_final)
        informe_id = await self._informe_de_trabajo(estudio_id, usuario_id)
        actual = await self._uno('SELECT version_edicion FROM public.radiologia_informe WHERE informe_id = :i FOR UPDATE', i=informe_id)
        if actual is not None and version_edicion != actual['version_edicion']:
            raise ConflictoRadiologia('Otra persona guardó este informe antes. Recarga para ver la versión actual.')
        plantilla = config.get('plantilla') or {}
        await self.db.execute(text('''INSERT INTO public.radiologia_informe
            (informe_id, plantilla_codigo, plantilla_version, contenido, texto_personalizado, version_edicion, updated_by)
            VALUES (:i, :pc, :pv, CAST(:c AS jsonb), :tp, 1, :u)
            ON CONFLICT (informe_id) DO UPDATE SET contenido = EXCLUDED.contenido, texto_personalizado = EXCLUDED.texto_personalizado,
                version_edicion = public.radiologia_informe.version_edicion + 1, updated_by = EXCLUDED.updated_by, updated_at = now()'''),
            {'i': informe_id, 'pc': plantilla.get('codigo', 'libre'), 'pv': plantilla.get('version', 1), 'c': _json(limpio),
             'tp': texto_final is not None, 'u': usuario_id})
        texto = texto_final if texto_final is not None else reglas.componer_informe(config, limpio)
        await self.db.execute(text('''UPDATE public.informe_imagen SET descripcion_texto = :t, updated_by = :u, updated_at = now()
            WHERE id = :i'''), {'t': texto or None, 'u': usuario_id, 'i': informe_id})
        await self._auditar(usuario_id, 'modificar', estudio_id, 'Borrador del informe guardado')

    async def validar(self, estudio_id: int, version_edicion: int, responsable: str, registro: str | None, usuario_id: int) -> None:
        await self._abierto(estudio_id, ('resultado_en_preparacion',))
        informe = await self._informe_actual(estudio_id)
        if informe is None or not informe['estructurado'] or informe['estado'] != 'borrador':
            raise ConflictoRadiologia('Guarda el informe antes de validarlo.')
        if informe['version_edicion'] != version_edicion:
            raise ConflictoRadiologia('El informe cambió desde que lo abriste. Recarga y revisa antes de validar.')
        faltan = reglas.pendientes_para_validar(informe['contenido'], informe['texto'], len(await self.imagenes(estudio_id)),
                                                bool(await self.informes_externos(estudio_id)))
        if faltan:
            raise ConflictoRadiologia('El informe todavía no se puede validar.', faltan)
        await self.db.execute(text('''UPDATE public.radiologia_informe SET responsable_nombre = :r, registro_profesional = :reg,
            updated_by = :u, updated_at = now() WHERE informe_id = :i'''),
            {'r': responsable, 'reg': registro, 'u': usuario_id, 'i': informe['id']})
        await self.db.execute(text('''UPDATE public.informe_imagen SET estado = 'publicado', usuario_publicacion_id = :u,
            fecha_hora_publicacion = now(), updated_by = :u, updated_at = now() WHERE id = :i'''), {'u': usuario_id, 'i': informe['id']})
        await self._cambiar_estado(estudio_id, 'publicado', usuario_id)
        await self._auditar(usuario_id, 'publicar', estudio_id, f'Informe validado por {responsable}', version=informe['numero_version'])

    async def agregar_adenda(self, estudio_id: int, motivo: str, texto_adenda: str, autor: str, registro: str | None, usuario_id: int) -> None:
        await self._abierto(estudio_id, ('publicado',))
        informe = await self._informe_actual(estudio_id)
        if informe is None or informe['estado'] != 'publicado':
            raise ConflictoRadiologia('Solo se agregan adendas a informes validados.')
        await self.db.execute(text('''INSERT INTO public.radiologia_adenda (informe_id, motivo, texto, usuario_id, autor_nombre, registro_profesional)
            VALUES (:i, :m, :t, :u, :a, :r)'''), {'i': informe['id'], 'm': motivo, 't': texto_adenda, 'u': usuario_id, 'a': autor, 'r': registro})
        await self._auditar(usuario_id, 'rectificar', estudio_id, f'Adenda agregada por {autor}: {motivo}')

    async def entregar(self, estudio_id: int, entregado_a: str, usuario_id: int) -> None:
        await self._abierto(estudio_id, ('publicado',))
        await self.db.execute(text('''INSERT INTO public.radiologia_estudio_detalle (estudio_id, entregado_en, entregado_por, entregado_a, created_by)
            VALUES (:e, now(), :u, :a, :u) ON CONFLICT (estudio_id) DO UPDATE SET entregado_en = now(),
            entregado_por = EXCLUDED.entregado_por, entregado_a = EXCLUDED.entregado_a
            WHERE public.radiologia_estudio_detalle.entregado_en IS NULL'''), {'e': estudio_id, 'u': usuario_id, 'a': entregado_a})
        await self._auditar(usuario_id, 'modificar', estudio_id, f'Informe entregado a {entregado_a}')

    # ---------- informes externos ----------

    async def agregar_externo(self, estudio_id: int, archivo: dict, datos: dict, usuario_id: int) -> None:
        await self._abierto(estudio_id, ESTADOS_ABIERTOS + ('publicado',))
        await self.db.execute(text('''INSERT INTO public.radiologia_informe_externo
            (estudio_id, nombre_original, url_archivo, mime_type, tamano_bytes, hash_sha256, establecimiento, profesional,
             fecha_informe, observaciones, cargado_por)
            VALUES (:e, :n, :url, :m, :t, :h, :est, :prof, :fecha, :obs, :u)'''),
            {'e': estudio_id, 'n': archivo['nombre_original'], 'url': archivo['url_archivo'], 'm': archivo['mime_type'],
             't': archivo['tamano_bytes'], 'h': archivo['hash_sha256'], 'est': datos['establecimiento'],
             'prof': datos.get('profesional'), 'fecha': datos.get('fecha_informe'), 'obs': datos.get('observaciones'), 'u': usuario_id})
        await self._auditar(usuario_id, 'crear', estudio_id, f'Informe externo adjuntado ({datos["establecimiento"]})')

    async def retirar_externo(self, estudio_id: int, externo_id: int, motivo: str, usuario_id: int) -> None:
        await self.base(estudio_id)
        fila = await self._uno('''UPDATE public.radiologia_informe_externo SET activo = false, motivo_retiro = :m
            WHERE id = :x AND estudio_id = :e AND activo RETURNING id''', m=motivo, x=externo_id, e=estudio_id)
        if fila is None:
            raise EstudioNoEncontrado('El informe externo no pertenece a este estudio')
        await self._auditar(usuario_id, 'anular', estudio_id, f'Informe externo retirado: {motivo}')

    async def externo(self, externo_id: int) -> dict | None:
        return await self._uno('''SELECT x.id, x.estudio_id, x.nombre_original, x.url_archivo, x.mime_type, e.estado
              FROM public.radiologia_informe_externo x JOIN public.estudio_solicitado e ON e.id = x.estudio_id
             WHERE x.id = :x AND x.activo''', x=externo_id)


def _config_generica(nombre: str) -> dict:
    """Estudios antiguos sin configuracion: plantilla libre con los campos generales."""
    from app.imagenes.domain.catalogo_radiologia import CAMPOS_GENERALES, VERSION_CATALOGO, _campo_dict
    return {
        'version': VERSION_CATALOGO, 'categoria': None, 'region': nombre, 'descripcion': '', 'requiere_lateralidad': False,
        'permite_bilateral': False, 'detalle_requerido': '', 'proyecciones': [], 'protocolos': [],
        'plantilla': {'codigo': 'libre', 'nombre': 'Informe libre', 'version': VERSION_CATALOGO,
                      'generales': [_campo_dict(c) for c in CAMPOS_GENERALES],
                      'apartados': [{'clave': 'hallazgos', 'titulo': 'Hallazgos', 'tipo': 'texto', 'ayuda': ''}]},
        'fuente': '', 'notas': [],
    }
