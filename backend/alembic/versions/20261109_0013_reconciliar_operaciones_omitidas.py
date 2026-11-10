"""Reconcilia operaciones omitidas por los dos padres distribuidos de RAG0008.

Conserva el grafo distribuido de main y verifica el contrato físico: la revisión
registrada por sí sola no prueba que Laboratorio/Ecografía estén materializados.
No reescribe tracking, informes ni revisiones. Los estados parciales ambiguos
fallan dentro de la transacción antes de registrar esta revisión.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import hashlib
import json

from alembic import op
import sqlalchemy as sa

revision = '20261109_0013'
down_revision = '20261109_0012'
branch_labels = None
depends_on = None

# Contratos normalizados obtenidos de las revisiones históricas exactas en
# PostgreSQL16/pgvector, sin datos ni OIDs. La matriz los contrasta en cada origen.
CONTRATOS = {
    'incidencia_muestra': '64614b5497da805a69743485981e14eed02b74c337c741d4e65f4970c1d6768a',
    'rag_torax_documento': 'dd12cf2694ae560f63de8365bce489f55f82183ceeae045117ade4ebdba5cbbb',
    'rag_torax_fragmento': 'cca033a6cbf48da90ac2ce0486ab0efffb8bc4b8e7e05810742f2b5dfed36ef7',
    'imagen_analisis_ia': '91d538b698b769ce279d77d6cfaa48c47b237c1fb96ab7332c8fe04a69bc7606',
    'imagen_revision_ia': 'b8309a71480b5d6cefad956a5770a6be3fc6ea53679fc965c496b73307485e49',
}


def historica(nombre):
    ruta = Path(__file__).with_name(nombre)
    spec = spec_from_file_location('_reconciliacion_' + ruta.stem, ruta)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def detener():
    raise RuntimeError(
        'Reconciliacion detenida: contrato parcial o incompatible. '
        'Revisar metadatos en una copia aislada; no usar stamp ni downgrade.'
    )


def columnas(bind, esperadas):
    """Todo ausente permite aplicar DDL original; todo presente exige su tipo."""
    presentes = []
    inspector = sa.inspect(bind)
    for tabla, nombre, tipo in esperadas:
        encontrada = next((c for c in inspector.get_columns(tabla, schema='public')
                           if c['name'] == nombre), None)
        if encontrada and not isinstance(encontrada['type'], tipo):
            detener()
        presentes.append(encontrada is not None)
    if any(presentes) and not all(presentes):
        detener()
    return all(presentes)


def validar_formatos(bind, lab9):
    """Exigir al menos una versión histórica completa, sin tocar la activa local."""
    for formato, adiciones in lab9.ADICIONES.items():
        versiones = bind.execute(sa.text('''SELECT v.id FROM public.plantilla_examen_version v
            JOIN public.plantilla_examen e ON e.id=v.plantilla_examen_id
            WHERE e.codigo=:codigo ORDER BY v.numero_version'''), {'codigo': formato}).scalars().all()
        valido = False
        for version in versiones:
            filas = bind.execute(sa.text('SELECT * FROM public.parametro_plantilla WHERE plantilla_version_id=:v'), {'v': version}).mappings().all()
            parametros = {p['codigo']: p for p in filas}
            if len(parametros) != len(filas):
                detener()
            if formato == 'FORM_QUIMICA_SANGUINEA' and 'bun' in parametros:
                continue
            coincide = True
            for codigo, nombre, tipo, unidad, referencia, _ in adiciones:
                p = parametros.get(codigo)
                if p is None or (p['nombre'], p['tipo_entrada'], p['unidad'], p['rango_referencia_texto']) != (nombre, tipo, unidad, referencia):
                    coincide = False
            for codigo, valores in lab9.CAMBIOS[formato].items():
                p = parametros.get(codigo)
                if p is None or any(valor is not None and p[campo] != valor
                                    for campo, valor in zip(('nombre', 'tipo_entrada', 'unidad', 'rango_referencia_texto'), valores)):
                    coincide = False
            for codigo, etiquetas in lab9.OPCIONES.items():
                if codigo in parametros:
                    opciones = bind.execute(sa.text('SELECT etiqueta FROM public.opcion_parametro WHERE parametro_id=:p ORDER BY orden'), {'p': parametros[codigo]['id']}).scalars().all()
                    if tuple(opciones) != etiquetas:
                        coincide = False
            if coincide:
                valido = True
                break
        if not valido:
            detener()


def huella_tabla(bind, tabla):
    """Contrato PostgreSQL16 sin OIDs, datos, propietarios ni valores de secuencia.

    Incluye nullability, identidad, PK/FK/checks, índices y funciones/triggers:
    comprobar solo nombres de tablas permitiría perder inmutabilidad histórica.
    """
    consultas = (
        '''SELECT a.attname,format_type(a.atttypid,a.atttypmod),a.attnotnull,
            a.attidentity::text,pg_get_expr(d.adbin,d.adrelid)
            FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
            WHERE a.attrelid=to_regclass(:tabla) AND a.attnum>0 AND NOT a.attisdropped
            ORDER BY a.attname''',
        '''SELECT conname,contype::text,pg_get_constraintdef(oid)
            FROM pg_constraint WHERE conrelid=to_regclass(:tabla) ORDER BY conname''',
        '''SELECT c.relname,pg_get_indexdef(i.indexrelid)
            FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid
            WHERE i.indrelid=to_regclass(:tabla) ORDER BY c.relname''',
        '''SELECT t.tgname,pg_get_triggerdef(t.oid),t.tgenabled::text,
            pg_get_functiondef(t.tgfoid) FROM pg_trigger t
            WHERE t.tgrelid=to_regclass(:tabla) AND NOT t.tgisinternal ORDER BY t.tgname''',
    )
    contrato = [[tuple(r) for r in bind.execute(sa.text(q), {'tabla': 'public.'+tabla})]
                for q in consultas]
    return hashlib.sha256(json.dumps(contrato, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()


def upgrade():
    bind = op.get_bind()
    # No usar IF NOT EXISTS para silenciar objetos de forma incompatible.
    lab8 = columnas(bind, [('paciente', 'telefono', sa.Text),
                            ('solicitud', 'procedencia', sa.Text)])
    if not lab8:
        historica('20261102_0008_datos_pedido_laboratorio.py').upgrade()
    else:
        procedencia = next(c for c in sa.inspect(bind).get_columns('solicitud', schema='public') if c['name'] == 'procedencia')
        if procedencia['nullable'] or 'este_centro' not in (procedencia['default'] or ''):
            detener()
        checks = sa.inspect(bind).get_check_constraints('solicitud', schema='public')
        if not any(c['name'] == 'ck_solicitud_procedencia'
                   and 'este_centro' in c['sqltext'] and 'otro_centro' in c['sqltext'] for c in checks):
            detener()

    lab9 = historica('20261102_0009_parametros_validados_laboratorio.py')
    encontrados = []
    for formato, adiciones in lab9.ADICIONES.items():
        for codigo, *_ in adiciones:
            encontrados.append(bind.execute(sa.text('''
                SELECT EXISTS(SELECT 1 FROM public.parametro_plantilla p
                JOIN public.plantilla_examen_version v ON v.id=p.plantilla_version_id
                JOIN public.plantilla_examen e ON e.id=v.plantilla_examen_id
                WHERE e.codigo=:formato AND p.codigo=:codigo)
            '''), {'formato': formato, 'codigo': codigo}).scalar_one())
    if any(encontrados) and not all(encontrados):
        detener()
    if not any(encontrados):
        lab9.upgrade()
    validar_formatos(bind, lab9)

    lab10 = columnas(bind, [('muestra', 'responsable_recepcion', sa.Text),
                             ('resultado_laboratorio', 'responsable_analisis', sa.Text),
                             ('version_resultado', 'responsable_publicacion', sa.Text)])
    tabla = sa.inspect(bind).has_table('incidencia_muestra', schema='public')
    if lab10 != tabla:
        detener()
    if not lab10:
        historica('20261102_0010_responsables_incidencias_laboratorio.py').upgrade()
    else:
        inspector = sa.inspect(bind)
        if not columnas(bind, [('incidencia_muestra', 'estudio_id', sa.BigInteger),
                              ('incidencia_muestra', 'usuario_id', sa.BigInteger),
                              ('incidencia_muestra', 'motivo', sa.Text),
                              ('incidencia_muestra', 'descripcion', sa.Text),
                              ('incidencia_muestra', 'responsable', sa.Text),
                              ('incidencia_muestra', 'fecha_hora', sa.DateTime)]):
            detener()
        if {fk['referred_table'] for fk in inspector.get_foreign_keys('incidencia_muestra', schema='public')} != {'estudio_solicitado', 'usuario'}:
            detener()
        if 'ix_incidencia_muestra_estudio_fecha' not in {i['name'] for i in inspector.get_indexes('incidencia_muestra', schema='public')}:
            detener()

    estados = []
    for tabla, nombre in [('estudio_estado_historial', 'ck_eeh_estado_nuevo'),
                          ('estudio_solicitado', 'ck_estudio_estado')]:
        checks = sa.inspect(bind).get_check_constraints(tabla, schema='public')
        check = next((c for c in checks if c['name'] == nombre), None)
        if check is None:
            detener()
        estados.append('no_realizado' in check['sqltext'])
    vista = bind.execute(sa.text("SELECT pg_get_viewdef('public.vista_solicitud_estado'::regclass)")).scalar_one()
    estados.append('no_realizado' in vista)
    if any(estados) and not all(estados):
        detener()
    if not any(estados):
        historica('20261103_0011_estudios_no_realizados.py').upgrade()

    # Repetición deliberada SOLO del INSERT anti-duplicados; nunca su downgrade.
    if bind.execute(sa.text("SELECT count(*) FROM public.servicio WHERE codigo='IMG'")).scalar_one() != 1:
        detener()
    eco = historica('20261104_0012_ecografias.py')
    eco.upgrade()
    validas = bind.execute(sa.text('''SELECT count(*) FROM public.tipo_estudio e
        JOIN public.servicio s ON s.id=e.servicio_id WHERE s.codigo='IMG'
        AND e.codigo IN :codigos AND NOT e.requiere_muestra
        AND e.requiere_informe AND e.requiere_archivos
    ''').bindparams(sa.bindparam('codigos', expanding=True)),
        {'codigos': [c for c, _ in eco.ECOGRAFIAS]}).scalar_one()
    if validas != len(eco.ECOGRAFIAS):
        detener()
    # IA/RAG no se recrean ni se alteran: su ausencia es inconsistencia.
    for tabla in ('rag_torax_documento', 'rag_torax_fragmento',
                  'imagen_analisis_ia', 'imagen_revision_ia'):
        if not sa.inspect(bind).has_table(tabla, schema='public'):
            detener()
    if not bind.execute(sa.text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar_one():
        detener()
    for tabla, esperado in CONTRATOS.items():
        if huella_tabla(bind, tabla) != esperado:
            detener()


def downgrade():
    raise RuntimeError('Reconciliacion de datos historicos: downgrade bloqueado.')
