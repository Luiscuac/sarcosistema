"""Flujos HTTP con login, repositorios y PostgreSQL reales, rollback y disco temporal."""
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import get_db
from app.config.settings import settings
from app.main import app

PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082')


@pytest.fixture
async def flujo_real(monkeypatch, tmp_path, client):
    from scripts import preparar_medico_demo as demo
    sufijo = uuid4().hex[:12]
    for nombre in ('USUARIO_DEMO', 'TRABAJADOR_DEMO', 'ESPECIALIDAD_DEMO', 'PACIENTE_DEMO'):
        monkeypatch.setattr(demo, nombre, getattr(demo, nombre) + sufijo)
    monkeypatch.setattr(settings, 'imagenes_storage_dir', str(tmp_path))
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    async with engine.connect() as conn:
        tx = await conn.begin()
        try:
            async with AsyncSession(bind=conn, expire_on_commit=False) as db:
                clave = 'clave-ficticia-exclusiva-de-pruebas'
                hash_ficticio = Argon2PasswordHasher().hashear(clave)
                await demo.preparar_medico_demo(db, hash_ficticio)
                nombres = {'medico': demo.USUARIO_DEMO}
                for rol in ('imagenes', 'laboratorio'):
                    trabajador = await db.scalar(text("INSERT INTO trabajador(identificador,nombre_completo,estado,fecha_inicio) VALUES (:i,'Profesional FICTICIO','activo',CURRENT_DATE) RETURNING id"), {'i': rol+sufijo})
                    nombres[rol] = rol+sufijo
                    await db.execute(text("INSERT INTO usuario(identificador_acceso,contrasena_hash,rol_id,trabajador_id,estado) SELECT :i,:h,id,:t,'activo' FROM rol WHERE codigo=:r"), {'i': nombres[rol], 'h': hash_ficticio, 't': trabajador, 'r': rol})

                async def db_real():
                    yield db

                app.dependency_overrides[get_db] = db_real
                headers = {}
                for rol, nombre in nombres.items():
                    login = await client.post('/accesos/login', json={'identificador_acceso': nombre, 'password': clave})
                    assert login.status_code == 200
                    headers[rol] = {'Authorization': 'Bearer ' + login.json()['access_token']}
                paciente = await db.scalar(text('SELECT id FROM paciente WHERE codigo_paciente=:c'), {'c': demo.PACIENTE_DEMO})
                medico = await db.scalar(text('SELECT m.id FROM medico m JOIN usuario u ON u.trabajador_id=m.trabajador_id WHERE u.identificador_acceso=:n'), {'n': demo.USUARIO_DEMO})
                yield client, db, headers, paciente, medico
        finally:
            app.dependency_overrides.pop(get_db, None)
            await tx.rollback()
    await engine.dispose()


async def test_ecografia_real_solicitar_publicar_consultar_y_descargar(flujo_real):
    client, db, h, paciente, _ = flujo_real
    catalogo = await client.get('/consultas/catalogo-imagenes', headers=h['medico'])
    assert catalogo.status_code == 200
    tipo = next(t['id'] for t in catalogo.json() if t['codigo'] == 'ECO_ABDOMINAL')
    solicitud = await client.post('/consultas/estudios-imagen', headers=h['medico'], json={
        'paciente_id': paciente, 'tipo_estudio_ids': [tipo],
        'medico_solicitante_nombre': 'Profesional FICTICIO', 'clave_idempotencia': str(uuid4()),
    })
    assert solicitud.status_code == 201, solicitud.text
    estudio = await db.scalar(text('SELECT id FROM estudio_solicitado WHERE solicitud_id=:s'), {'s': solicitud.json()['solicitud_id']})
    assert (await client.get('/imagenes/bandeja', headers=h['medico'])).status_code == 403
    assert (await client.get('/imagenes/analisis/estudios', headers=h['imagenes'])).status_code == 403
    bandeja = await client.get('/imagenes/bandeja', headers=h['imagenes'])
    assert any(e['estudio_id'] == estudio for e in bandeja.json())
    guardado = await client.post(f'/imagenes/estudios/{estudio}/informes', headers=h['imagenes'],
        data={'descripcion': 'INFORME DE ECOGRAFIA FICTICIO'}, files={'archivos': ('eco.png', PNG, 'image/png')})
    assert guardado.status_code == 200, guardado.text
    historial = await client.get(f'/consultas/pacientes/{paciente}/historial', headers=h['medico'])
    assert historial.status_code == 200, historial.text
    assert historial.json()['estudios_imagen'] == []
    publicado = await client.post(f'/imagenes/estudios/{estudio}/informes/publicar', headers=h['imagenes'])
    assert publicado.status_code == 200, publicado.text
    historial = await client.get(f'/consultas/pacientes/{paciente}/historial', headers=h['medico'])
    entrada = next(e for e in historial.json()['estudios_imagen'] if e['estudio_id'] == estudio)
    assert entrada['descripcion_texto'] == 'INFORME DE ECOGRAFIA FICTICIO'
    archivo = entrada['archivos'][0]['id']
    descarga = await client.get(f'/imagenes/archivos/{archivo}', headers=h['medico'])
    assert descarga.status_code == 200, descarga.text
    assert descarga.content == PNG


async def test_laboratorio_real_muestra_borrador_publicacion_y_consulta_medica(flujo_real):
    client, db, h, paciente, medico = flujo_real
    catalogo = await client.get('/laboratorio/catalogo/estudios', headers=h['laboratorio'])
    assert catalogo.status_code == 200
    # Formato pequeño real, no se reemplaza el catálogo por un doble.
    tipo = await db.scalar(text("SELECT t.id FROM tipo_estudio t JOIN servicio s ON s.id=t.servicio_id WHERE s.codigo='LAB' AND t.codigo='GLUCOSA'"))
    if tipo is None:
        tipo = next(e['id'] for e in catalogo.json() if e['plantilla_configurada'])
    solicitud = await client.post('/laboratorio/solicitudes', headers=h['laboratorio'], json={
        'paciente_id': paciente, 'tipo_estudio_ids': [tipo], 'medico_solicitante_id': medico,
        'medico_solicitante_nombre': 'Profesional FICTICIO', 'clave_idempotencia': str(uuid4()),
    })
    assert solicitud.status_code == 201, solicitud.text
    sid = solicitud.json()['id']
    estudio = solicitud.json()['estudios'][0]['id']
    muestra = await client.post(f'/laboratorio/solicitudes/{sid}/muestras', headers=h['laboratorio'], json={
        'estudio_ids': [estudio], 'tipo_muestra': 'Sangre', 'fecha_toma': date.today().isoformat(),
        'hora_no_registrada': True, 'responsable_recepcion': 'Profesional FICTICIO',
    })
    assert muestra.status_code == 201, muestra.text
    resultado = await client.get(f'/laboratorio/estudios/{estudio}/resultado', headers=h['laboratorio'])
    assert resultado.status_code == 200, resultado.text
    valores = [{'parametro_id': p['id'], 'valor': p['opciones'][0] if p['opciones'] else ('90' if p['tipo_entrada'] in ('entero','decimal','numero') else 'FICTICIO')} for p in resultado.json()['parametros']]
    borrador = await client.put(f'/laboratorio/estudios/{estudio}/resultado/borrador', headers=h['laboratorio'], json={
        'valores': valores, 'responsable_analisis': 'Profesional FICTICIO', 'observaciones': 'PRUEBA FICTICIA',
    })
    assert borrador.status_code == 200, borrador.text
    oculto = await client.get(f'/laboratorio/medicos/solicitudes/{sid}/informe', headers=h['medico'])
    assert oculto.status_code in (404, 409)
    publicado = await client.post(f'/laboratorio/estudios/{estudio}/resultado/publicar', headers=h['laboratorio'], json={'responsable_publicacion': 'Profesional FICTICIO'})
    assert publicado.status_code == 200, publicado.text
    informe = await client.get(f'/laboratorio/medicos/solicitudes/{sid}/informe', headers=h['medico'])
    assert informe.status_code == 200, informe.text
    assert informe.json()['resultados']
    assert (await client.get('/laboratorio/catalogo/estudios', headers=h['imagenes'])).status_code == 403
    # Un análisis de laboratorio publicado no es un examen de imagen: no debe listarse como ecografía.
    historial = await client.get(f'/consultas/pacientes/{paciente}/historial', headers=h['medico'])
    assert historial.status_code == 200, historial.text
    assert estudio not in [e['estudio_id'] for e in historial.json()['estudios_imagen']]
