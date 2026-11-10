"""Ensayo real optativo: solo bases ficticias nuevas en un servidor aislado.

MIGRATION_TEST_ADMIN_URL debe identificar la BD integration_admin de un
contenedor de pruebas, nunca una instalación clínica. No usa stamp ni downgrade.
"""
import asyncio
import os
from pathlib import Path
import shutil
import uuid

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND = Path(__file__).resolve().parents[1]
CORRECTIVA = '20261109_0013'
PERFILES = (
    ('vacia', None), ('laboratorio_8', '20261102_0008'),
    ('laboratorio_9', '20261102_0009'), ('laboratorio_10', '20261102_0010'),
    ('laboratorio_11', '20261103_0011'),
    ('ia_original_8', '20261103_0008'), ('ia_original_9', '20261103_0009'),
    ('union_original', '20261109_0012'),
    ('ia_original_lab8_doble', '20261103_0009'),
    ('ia_original_lab11_doble', '20261103_0009'),
    ('main_ecografia', '20261104_0012'), ('main_rag', '20261103_0008'),
    ('main_ia', '20261103_0009'),
)


@pytest.fixture(scope='module')
def contratos_observados():
    return []


def scripts_en(tmp_path, perfil='final'):
    destino = tmp_path / perfil
    shutil.copytree(BACKEND / 'alembic', destino, ignore=shutil.ignore_patterns('__pycache__'))
    for ruta in (destino / 'versions').glob('*.py'):
        nombre = ruta.name
        if perfil != 'final' and nombre.startswith(CORRECTIVA):
            ruta.unlink()
        if perfil.startswith(('ia_original', 'union_original', 'laboratorio')):
            if nombre.startswith('20261104_0012'):
                ruta.unlink()
                continue
        if perfil.startswith('laboratorio') and nombre.startswith(('20261103_0008', '20261103_0009', '20261109_0012')):
            ruta.unlink()
    rag = destino / 'versions' / '20261103_0008_rag_torax.py'
    if rag.exists():
        texto = rag.read_text(encoding='utf-8')
        padre = '20261027_0007' if perfil.startswith(('ia_original', 'union_original')) else '20261104_0012'
        import re
        texto = re.sub(r"down_revision = '[^']+'", f"down_revision = '{padre}'", texto)
        rag.write_text(texto, encoding='utf-8')
    # Usar env.py real: el mismo que ejecutarán instalaciones y preparador.
    config = Config()
    config.set_main_option('script_location', str(destino))
    return config


def test_correctiva_se_programa_desde_ambas_revisiones_ia(tmp_path):
    scripts = ScriptDirectory.from_config(scripts_en(tmp_path))
    assert scripts.get_heads() == [CORRECTIVA]
    for origen in ('20261103_0008', '20261103_0009', '20261109_0012', '20261104_0012'):
        pasos = scripts._upgrade_revs('heads', origen)
        assert CORRECTIVA in [p.revision.revision for p in pasos]


@pytest.fixture
async def base_aislada():
    if os.getenv('RUN_MIGRATION_MATRIX') != '1':
        pytest.skip('Matriz PostgreSQL aislada optativa')
    from urllib.parse import urlparse
    url = os.environ['MIGRATION_TEST_ADMIN_URL']
    parsed = urlparse(url)
    if parsed.hostname not in ('127.0.0.1', 'localhost') or parsed.path != '/integration_admin':
        pytest.fail('La matriz requiere integration_admin aislada en loopback')
    admin = await asyncpg.connect(url)
    nombre = 'integration_' + uuid.uuid4().hex
    await admin.execute(f'CREATE DATABASE "{nombre}"')
    await admin.close()
    url_base = url.rsplit('/', 1)[0] + '/' + nombre
    conn = await asyncpg.connect(url_base)
    await conn.execute((BACKEND.parent / 'database/schema.sql').read_text(encoding='utf-8'))
    await conn.close()
    yield url_base
    # Se conservan las bases ficticias para inspección; nunca se borra una BD.


async def migrar(config, url, revision):
    config.set_main_option('sqlalchemy.url', url.replace('postgresql://', 'postgresql+asyncpg://'))
    await asyncio.to_thread(command.upgrade, config, revision)


async def actualizar_final(config, url):
    from scripts.reconciliar_historial_imagenes import actualizar
    config.set_main_option('sqlalchemy.url', url.replace('postgresql://', 'postgresql+asyncpg://'))
    await asyncio.to_thread(actualizar, config)


async def contrato(conn):
    columnas = await conn.fetch('''SELECT table_name,column_name,data_type,is_nullable,
        column_default FROM information_schema.columns WHERE table_schema='public'
        AND table_name <> 'alembic_version' ORDER BY 1,2''')
    constraints = await conn.fetch('''SELECT c.relname, con.conname,
        pg_get_constraintdef(con.oid) FROM pg_constraint con
        JOIN pg_class c ON c.oid=con.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname<>'alembic_version' ORDER BY 1,2''')
    indices = await conn.fetch("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' AND tablename<>'alembic_version' ORDER BY 1,2")
    vistas = await conn.fetch("SELECT viewname,definition FROM pg_views WHERE schemaname='public' ORDER BY 1")
    triggers = await conn.fetch("SELECT event_object_table,trigger_name,action_statement FROM information_schema.triggers WHERE trigger_schema='public' ORDER BY 1,2,3")
    return [list(map(tuple, grupo)) for grupo in (columnas, constraints, indices, vistas, triggers)]


async def sembrar_clinica(conn):
    trabajador = await conn.fetchval("INSERT INTO trabajador(identificador,nombre_completo,estado,fecha_inicio) VALUES ('INTEGRACION-FICTICIA','Profesional ficticio','activo',CURRENT_DATE) RETURNING id")
    usuario = await conn.fetchval("INSERT INTO usuario(identificador_acceso,contrasena_hash,rol_id,trabajador_id,estado) SELECT 'integracion_ficticia','hash-ficticio',id,$1,'activo' FROM rol WHERE codigo='medico' RETURNING id", trabajador)
    medico = await conn.fetchval("INSERT INTO medico(trabajador_id,matricula_profesional,activo) VALUES ($1,'FICTICIA',true) RETURNING id", trabajador)
    paciente = await conn.fetchval("SELECT id FROM paciente WHERE codigo_paciente='PAC-INTEGRACION-FICTICIO'")
    servicio = await conn.fetchval("SELECT id FROM servicio WHERE codigo='IMG'")
    tipo = await conn.fetchval("INSERT INTO tipo_estudio(codigo,nombre,servicio_id,requiere_informe,requiere_archivos) VALUES ('RX-FICTICIO','Ficticio',$1,true,true) RETURNING id", servicio)
    solicitud = await conn.fetchval("INSERT INTO solicitud(referencia,paciente_id,fecha_solicitud,medico_solicitante_id,prioridad) VALUES ('FICTICIA',$1,now(),$2,'sin_prioridad') RETURNING id", paciente, medico)
    estudio = await conn.fetchval("INSERT INTO estudio_solicitado(referencia,solicitud_id,paciente_id,servicio_id,tipo_estudio_id,estado) VALUES ('RX-FICTICIO',$1,$2,$3,$4,'publicado') RETURNING id", solicitud, paciente, servicio, tipo)
    informe = await conn.fetchval("INSERT INTO informe_imagen(estudio_id,numero_version,descripcion_texto,estado,usuario_publicacion_id,fecha_hora_publicacion) VALUES ($1,1,'INFORME FICTICIO HISTORICO','publicado',$2,now()) RETURNING id", estudio, usuario)
    archivo = await conn.fetchval("INSERT INTO archivo_imagen(informe_id,nombre_original,url_archivo,mime_type,tamano_bytes,hash_sha256,fecha_carga,created_by) VALUES ($1,'ficticio.png','ficticio.png','image/png',10,$2,now(),$3) RETURNING id", informe, 'a'*64, usuario)
    if await conn.fetchval("SELECT to_regclass('public.rag_torax_documento') IS NOT NULL"):
        await conn.execute("INSERT INTO rag_torax_documento(id,titulo,fuente,licencia,categoria,version,sha256,contenido) VALUES ('ficticio','Ficticio','local','ficticia','torax','1',$1,'Documento ficticio')", 'b'*64)
        await conn.execute("INSERT INTO rag_torax_fragmento(id,documento_id,seccion,inicio,fin,texto,modelo,embedding) VALUES ('ficticio','ficticio','Ficticia',0,8,'Ficticio','ficticio',$1::vector)", '[' + ','.join(['1'] + ['0']*383) + ']')
    if await conn.fetchval("SELECT to_regclass('public.imagen_analisis_ia') IS NOT NULL"):
        analisis = uuid.uuid4()
        await conn.execute("INSERT INTO imagen_analisis_ia(id,estudio_id,informe_id,archivo_id,solicitado_por,clave,proyeccion,informe_texto,informe_sha256,archivo_sha256,estado,resultado) VALUES ($1,$2,$3,$4,$5,'ficticia','PA','INFORME FICTICIO HISTORICO',$6,$7,'completado','{}')", analisis, estudio, informe, archivo, usuario, 'c'*64, 'a'*64)
        await conn.execute("INSERT INTO imagen_revision_ia(analisis_id,usuario_id,version,decision,motivo) VALUES ($1,$2,1,'rechazada','Revision ficticia')", analisis, usuario)


async def filas_clinicas(conn):
    filas = {}
    for tabla in ('paciente','solicitud','estudio_solicitado','informe_imagen','archivo_imagen',
                  'rag_torax_documento','rag_torax_fragmento','imagen_analisis_ia','imagen_revision_ia'):
        if await conn.fetchval('SELECT to_regclass($1) IS NOT NULL', 'public.'+tabla):
            filas[tabla] = [dict(r) for r in await conn.fetch(f'SELECT * FROM public.{tabla} ORDER BY id')]
    return filas


@pytest.mark.parametrize('perfil,revision', PERFILES)
async def test_actualizacion_real_conserva_contrato_catalogos_y_datos(tmp_path, base_aislada, contratos_observados, perfil, revision):
    final = scripts_en(tmp_path)
    if revision:
        anterior = scripts_en(tmp_path, perfil)
        await migrar(anterior, base_aislada, revision)
        if perfil.endswith('_doble'):
            await migrar(anterior, base_aislada, '20261102_0008' if 'lab8_' in perfil else '20261103_0011')
    conn = await asyncpg.connect(base_aislada)
    await conn.execute("""INSERT INTO paciente (codigo_paciente,sin_documento,nombre_completo,fecha_nacimiento,sexo,estado)
        VALUES ('PAC-INTEGRACION-FICTICIO',true,'PACIENTE FICTICIO INTEGRACION','2000-01-01','F','activo')""")
    paciente = await conn.fetch('SELECT * FROM paciente ORDER BY id')
    if revision:
        await sembrar_clinica(conn)
    clinica = await filas_clinicas(conn)
    # Un nombre personalizado del catálogo existente tampoco debe sobrescribirse.
    if await conn.fetchval("SELECT EXISTS(SELECT 1 FROM tipo_estudio WHERE codigo='ECO_ABDOMINAL')"):
        await conn.execute("UPDATE tipo_estudio SET nombre='Nombre local ficticio' WHERE codigo='ECO_ABDOMINAL'")
    await conn.close()
    await actualizar_final(final, base_aislada)
    conn = await asyncpg.connect(base_aislada)
    despues = await conn.fetch('SELECT * FROM paciente ORDER BY id')
    for antes, ahora in zip(paciente, despues, strict=True):
        assert dict(antes).items() <= dict(ahora).items()
    for tabla, filas in clinica.items():
        actual = await conn.fetch(f'SELECT * FROM public.{tabla} ORDER BY id')
        for antes, ahora in zip(filas, actual, strict=True):
            assert antes.items() <= dict(ahora).items(), tabla
    assert await conn.fetchval('SELECT version_num FROM alembic_version') == CORRECTIVA
    assert await conn.fetchval("SELECT count(*) FROM tipo_estudio WHERE codigo LIKE 'ECO_%'") == 8
    assert await conn.fetchval("SELECT extversion IS NOT NULL FROM pg_extension WHERE extname='vector'")
    assert await conn.fetchval("SELECT '[1,0]'::vector <=> '[1,0]'::vector") == 0
    assert await conn.fetchval("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('rag_torax_documento','rag_torax_fragmento','imagen_analisis_ia','imagen_revision_ia','incidencia_muestra')") == 5
    assert await conn.fetchval("SELECT count(DISTINCT p.codigo) FROM parametro_plantilla p JOIN plantilla_examen_version v ON v.id=p.plantilla_version_id JOIN plantilla_examen e ON e.id=v.plantilla_examen_id WHERE e.codigo='FORM_HEMOGRAMA_COMPLETO' AND v.estado='activa' AND p.codigo IN ('vcm','mch','mchc','rdw_cv')") == 4
    huella = await contrato(conn)
    if contratos_observados:
        assert huella == contratos_observados[0]
    else:
        contratos_observados.append(huella)
    # upgrade repetido no cambia esquema, datos ni versiones de formatos.
    versiones = await conn.fetch('SELECT * FROM plantilla_examen_version ORDER BY id')
    await conn.close()
    await migrar(final, base_aislada, 'head')
    conn = await asyncpg.connect(base_aislada)
    assert await contrato(conn) == huella
    assert await conn.fetch('SELECT * FROM plantilla_examen_version ORDER BY id') == versiones
    if perfil in ('main_ecografia', 'main_rag', 'main_ia'):
        assert await conn.fetchval("SELECT nombre FROM tipo_estudio WHERE codigo='ECO_ABDOMINAL'") == 'Nombre local ficticio'
    await conn.close()


@pytest.mark.parametrize('alteracion', [
    'ALTER TABLE paciente ADD COLUMN telefono text',
    "UPDATE parametro_plantilla SET codigo='vcm' WHERE id=(SELECT min(id) FROM parametro_plantilla)",
])
async def test_contrato_parcial_aborta_sin_registrar_revision(tmp_path, base_aislada, alteracion):
    anterior = scripts_en(tmp_path, 'ia_original_9')
    await migrar(anterior, base_aislada, '20261103_0009')
    conn = await asyncpg.connect(base_aislada)
    await conn.execute(alteracion)
    antes = await contrato(conn)
    await conn.close()
    with pytest.raises(RuntimeError, match='contrato parcial'):
        await migrar(scripts_en(tmp_path), base_aislada, 'head')
    conn = await asyncpg.connect(base_aislada)
    assert await contrato(conn) == antes
    assert await conn.fetchval('SELECT version_num FROM alembic_version') == '20261103_0009'
    await conn.close()


@pytest.mark.parametrize('alteracion', [
    'ALTER TABLE solicitud ALTER COLUMN procedencia DROP NOT NULL',
    "UPDATE parametro_plantilla SET unidad='unidad-incompatible' WHERE codigo='vcm'",
])
async def test_no_confunde_presencia_con_contrato_valido(tmp_path, base_aislada, alteracion):
    await migrar(scripts_en(tmp_path, 'union_original'), base_aislada, '20261109_0012')
    conn = await asyncpg.connect(base_aislada)
    await conn.execute(alteracion)
    await conn.close()
    with pytest.raises(RuntimeError, match='contrato parcial'):
        await migrar(scripts_en(tmp_path), base_aislada, 'head')


async def test_preparador_respeta_destino_config_con_env_real(tmp_path, base_aislada, monkeypatch):
    from app.config.settings import settings
    final = scripts_en(tmp_path)
    destino = Path(final.get_main_option('script_location'))
    shutil.copyfile(BACKEND / 'alembic/env.py', destino / 'env.py')
    # Un destino distinto no disponible garantiza que no se consulta por error.
    monkeypatch.setattr(settings, 'database_url', 'postgresql+asyncpg://nadie@127.0.0.1:1/no_usar')
    await actualizar_final(final, base_aislada)
    conn = await asyncpg.connect(base_aislada)
    assert await conn.fetchval('SELECT version_num FROM alembic_version') == CORRECTIVA
    await conn.close()


async def test_dos_etapas_revierten_juntas_ante_contrato_incompatible(tmp_path, base_aislada):
    anterior = scripts_en(tmp_path, 'ia_original_lab8_doble')
    await migrar(anterior, base_aislada, '20261103_0009')
    await migrar(anterior, base_aislada, '20261102_0008')
    conn = await asyncpg.connect(base_aislada)
    await conn.execute('ALTER TABLE paciente ALTER COLUMN telefono TYPE bigint USING NULL')
    antes = await contrato(conn)
    versiones = await conn.fetch('SELECT * FROM plantilla_examen_version ORDER BY id')
    heads = await conn.fetch('SELECT version_num FROM alembic_version ORDER BY version_num')
    await conn.close()
    with pytest.raises(RuntimeError, match='contrato parcial'):
        await actualizar_final(scripts_en(tmp_path), base_aislada)
    conn = await asyncpg.connect(base_aislada)
    assert await contrato(conn) == antes
    assert await conn.fetch('SELECT * FROM plantilla_examen_version ORDER BY id') == versiones
    assert await conn.fetch('SELECT version_num FROM alembic_version ORDER BY version_num') == heads
    await conn.close()


@pytest.mark.parametrize('alteracion', [
    'DROP TRIGGER trg_revision_ia_historica ON imagen_revision_ia',
    'ALTER TABLE incidencia_muestra ALTER COLUMN motivo DROP NOT NULL',
    'ALTER TABLE rag_torax_fragmento DROP CONSTRAINT rag_torax_fragmento_documento_id_fkey',
])
async def test_rechaza_perdida_de_protecciones_historicas(tmp_path, base_aislada, alteracion):
    await migrar(scripts_en(tmp_path, 'union_original'), base_aislada, '20261109_0012')
    conn = await asyncpg.connect(base_aislada)
    await conn.execute(alteracion)
    await conn.close()
    with pytest.raises(RuntimeError, match='contrato parcial'):
        await actualizar_final(scripts_en(tmp_path), base_aislada)
