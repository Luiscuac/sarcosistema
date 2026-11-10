import hashlib
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from app.imagenes.infrastructure.persistence.repository import EstudiosRepository


@pytest.fixture
async def estudio_fixture(monkeypatch):
    from scripts import preparar_medico_demo as demo
    for nombre in ('USUARIO_DEMO','TRABAJADOR_DEMO','ESPECIALIDAD_DEMO','PACIENTE_DEMO'):
        monkeypatch.setattr(demo,nombre,getattr(demo,nombre)+'_'+uuid.uuid4().hex[:12])
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    async with engine.connect() as conn:
        tx = await conn.begin()
        async with AsyncSession(bind=conn, expire_on_commit=False) as db:
            await demo.preparar_medico_demo(db, 'hash-ficticio-integracion')
            usuario = await db.scalar(text('SELECT id FROM public.usuario WHERE identificador_acceso=:nombre'), {'nombre':demo.USUARIO_DEMO})
            medico = await db.scalar(text('SELECT m.id FROM public.medico m JOIN public.usuario u ON u.trabajador_id=m.trabajador_id WHERE u.id=:id'), {'id':usuario})
            paciente = await db.scalar(text('SELECT id FROM public.paciente WHERE codigo_paciente=:codigo'), {'codigo':demo.PACIENTE_DEMO})
            servicio = await db.scalar(text("SELECT id FROM public.servicio WHERE codigo='IMG'"))
            codigo = 'TEST-RX-'+uuid.uuid4().hex
            tipo = await db.scalar(text('INSERT INTO public.tipo_estudio(codigo,nombre,servicio_id,requiere_informe,requiere_archivos) VALUES (:c,\'Tórax ficticio\',:s,true,true) RETURNING id'), {'c':codigo,'s':servicio})
            solicitud = await db.scalar(text('INSERT INTO public.solicitud(referencia,paciente_id,fecha_solicitud,medico_solicitante_id,prioridad) VALUES (:r,:p,now(),:m,\'sin_prioridad\') RETURNING id'), {'r':codigo,'p':paciente,'m':medico})
            estudio = await db.scalar(text('INSERT INTO public.estudio_solicitado(referencia,solicitud_id,paciente_id,servicio_id,tipo_estudio_id,estado) VALUES (:r,:s,:p,:v,:t,\'publicado\') RETURNING id'), {'r':codigo,'s':solicitud,'p':paciente,'v':servicio,'t':tipo})
            informe = await db.scalar(text("INSERT INTO public.informe_imagen(estudio_id,numero_version,descripcion_texto,estado,usuario_publicacion_id,fecha_hora_publicacion) VALUES (:e,1,'Simulación: no se observa derrame pleural.','publicado',:u,now()) RETURNING id"), {'e':estudio,'u':usuario})
            archivo = await db.scalar(text("INSERT INTO public.archivo_imagen(informe_id,nombre_original,url_archivo,mime_type,tamano_bytes,hash_sha256,fecha_carga,created_by) VALUES (:i,'fixture.png','fixture.png','image/png',10,:h,now(),:u) RETURNING id"), {'i':informe,'h':'a'*64,'u':usuario})
            yield db, usuario, estudio, informe, archivo
        await tx.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_lectura_solo_medico_solicitante(estudio_fixture):
    db, usuario, estudio, _, archivo = estudio_fixture
    repo = EstudiosRepository(db)
    propio = await repo.obtener(estudio, usuario)
    assert propio['archivo']['id'] == archivo
    assert await repo.obtener(estudio, -1) is None
    assert (await repo.listar(-1, 1)) == []
    assert any(e['id'] == estudio for e in await repo.listar(usuario, 1))


@pytest.mark.asyncio
async def test_idempotencia_y_revision_no_modifican_informe(estudio_fixture):
    db, usuario, estudio, informe, _ = estudio_fixture
    repo = EstudiosRepository(db)
    snapshot = await repo.obtener(estudio, usuario)
    a = await repo.crear_analisis(snapshot, usuario, 'clave-prueba', 'PA')
    b = await repo.crear_analisis(snapshot, usuario, 'clave-prueba', 'PA')
    assert a['id'] == b['id']
    assert (await repo.obtener(estudio,usuario))['analisis_reciente'] == a['id']
    with pytest.raises(ValueError):
        await repo.crear_analisis(snapshot, usuario, 'clave-prueba', 'AP')
    await repo.finalizar(a['id'], {'experimental':True}, None)
    revision = await repo.registrar_revision(a['id'], usuario, 0, 'rechazada', 'Revisión ficticia', None)
    assert revision['version_revision'] == 1
    with pytest.raises(ValueError):
        await repo.registrar_revision(a['id'], usuario, 0, 'aceptada_como_propuesta', '', None)
    assert await repo.obtener_analisis(a['id'], -1) is None
    assert await db.scalar(text('SELECT descripcion_texto FROM public.informe_imagen WHERE id=:id'), {'id':informe}) == snapshot['informe_texto']


@pytest.mark.asyncio
async def test_reclamar_una_vez_y_recuperar_interrupcion(estudio_fixture):
    db, usuario, estudio, _, _ = estudio_fixture
    repo = EstudiosRepository(db)
    trabajo = await repo.crear_analisis(await repo.obtener(estudio,usuario),usuario,'interrupcion','PA')
    reclamado = await repo.reclamar()
    assert reclamado['id'] == trabajo['id']
    assert reclamado['estado'] == 'procesando'
    assert await repo.reclamar() is None
    await repo.finalizar(trabajo['id'],{'experimental':True},None,
        liderazgo={'pid':-1,'inicio':datetime.now(timezone.utc)})
    assert (await repo.obtener_analisis(trabajo['id'],usuario))['estado'] == 'procesando'
    await repo.recuperar_interrumpidos()
    assert (await repo.obtener_analisis(trabajo['id'],usuario))['estado'] == 'interrumpido'


@pytest.mark.asyncio
async def test_demo_declara_simulacion_y_no_reemplaza_datos(estudio_fixture,monkeypatch):
    from scripts import preparar_estudio_imagen_demo as demo
    monkeypatch.setattr(demo,'REFERENCIA','TEST-RX-DEMO-'+uuid.uuid4().hex)
    monkeypatch.setattr(demo,'PACIENTE_CODIGO','TEST-PAC-RX-'+uuid.uuid4().hex)
    db, usuario, _, _, _ = estudio_fixture
    archivo = dict(url_archivo='fixture.png',tamano_bytes=10,hash_sha256='a'*64)
    id = await demo.preparar_estudio_demo(db,usuario,archivo)
    detalle = await EstudiosRepository(db).obtener(id,usuario)
    assert 'SIMULACIÓN DE INTEGRACIÓN' in detalle['informe_texto']
    assert 'no es el informe auténtico' in detalle['informe_texto']
    with pytest.raises(ValueError,match='existe'):
        await demo.preparar_estudio_demo(db,usuario,archivo)
