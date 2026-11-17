"""Radiologia convencional de principio a fin: HTTP + login + PostgreSQL reales, rollback y disco temporal.

Casos: torax, rodilla derecha (lateralidad y plantilla distinta), columna lumbar, solicitud multiple,
borrador y validacion con permisos, imagenes y restricciones de acceso.
"""
import io
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import get_db
from app.config.settings import settings
from app.main import app

R = '/imagenes/radiologia'


def png(valor: int) -> bytes:
    from PIL import Image
    salida = io.BytesIO()
    imagen = Image.new('L', (48, 48), valor)
    imagen.putpixel((0, 0), 255 - valor)  # contraste minimo para la vista previa
    imagen.save(salida, format='PNG')
    return salida.getvalue()


@pytest.fixture
async def rx(monkeypatch, tmp_path, client):
    from scripts import preparar_medico_demo as demo
    sufijo = uuid4().hex[:12]
    for nombre in ('USUARIO_DEMO', 'TRABAJADOR_DEMO', 'ESPECIALIDAD_DEMO', 'PACIENTE_DEMO'):
        monkeypatch.setattr(demo, nombre, getattr(demo, nombre) + sufijo)
    monkeypatch.setattr(settings, 'imagenes_storage_dir', str(tmp_path))
    monkeypatch.setattr(settings, 'radiology_ai_enabled', False)
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    async with engine.connect() as conn:
        tx = await conn.begin()
        try:
            async with AsyncSession(bind=conn, expire_on_commit=False) as db:
                clave = 'clave-ficticia-exclusiva-de-pruebas'
                hash_ficticio = Argon2PasswordHasher().hashear(clave)
                await demo.preparar_medico_demo(db, hash_ficticio)
                nombres = {'medico': demo.USUARIO_DEMO}
                for rol in ('rayos_x', 'radiologo', 'laboratorio'):
                    trabajador = await db.scalar(text("INSERT INTO trabajador(identificador,nombre_completo,estado,fecha_inicio) VALUES (:i,'Profesional FICTICIO','activo',CURRENT_DATE) RETURNING id"), {'i': rol + sufijo})
                    nombres[rol] = rol + sufijo
                    await db.execute(text("INSERT INTO usuario(identificador_acceso,contrasena_hash,rol_id,trabajador_id,estado) SELECT :i,:h,id,:t,'activo' FROM rol WHERE codigo=:r"), {'i': nombres[rol], 'h': hash_ficticio, 't': trabajador, 'r': rol})

                async def db_real():
                    yield db

                app.dependency_overrides[get_db] = db_real
                h = {}
                for rol, nombre in nombres.items():
                    login = await client.post('/accesos/login', json={'identificador_acceso': nombre, 'password': clave})
                    assert login.status_code == 200
                    h[rol] = {'Authorization': 'Bearer ' + login.json()['access_token']}
                paciente = await db.scalar(text('SELECT id FROM paciente WHERE codigo_paciente=:c'), {'c': demo.PACIENTE_DEMO})
                medico = await db.scalar(text('SELECT m.id FROM medico m JOIN usuario u ON u.trabajador_id=m.trabajador_id WHERE u.identificador_acceso=:n'), {'n': demo.USUARIO_DEMO})
                catalogo = (await client.get(f'{R}/catalogo', headers=h['rayos_x'])).json()
                tipos = {e['codigo']: e for e in catalogo['estudios']}
                yield {'c': client, 'db': db, 'h': h, 'paciente': paciente, 'medico': medico, 'tipos': tipos, 'catalogo': catalogo}
        finally:
            app.dependency_overrides.pop(get_db, None)
            await tx.rollback()
    await engine.dispose()


async def solicitar(rx, estudios, rol='rayos_x', **extra):
    cuerpo = {'paciente_id': rx['paciente'], 'prioridad': 'sin_prioridad', 'procedencia': 'este_centro',
              'medico_solicitante_id': rx['medico'], 'clave_idempotencia': str(uuid4()), 'estudios': estudios} | extra
    return await rx['c'].post(f'{R}/solicitudes', json=cuerpo, headers=rx['h'][rol])


async def adquirir(rx, estudio_id, proyecciones, lateralidad=None, imagenes=(10, 20)):
    c, h = rx['c'], rx['h']['rayos_x']
    archivos = [('archivos', (f'img{i}.png', png(v + estudio_id % 50), 'image/png')) for i, v in enumerate(imagenes)]
    datos = [('proyecciones', p) for p in proyecciones[:len(imagenes)]]
    subida = await c.post(f'{R}/estudios/{estudio_id}/imagenes', files=archivos, data=dict(proyecciones=[p for _, p in datos]), headers=h)
    assert subida.status_code == 200, subida.text
    registro = await c.put(f'{R}/estudios/{estudio_id}/adquisicion', headers=h, json={
        'proyecciones_realizadas': proyecciones, 'lateralidad_realizada': lateralidad, 'posicion_paciente': 'bipedestacion',
        'fecha_hora_adquisicion': '2026-11-16T15:00:00Z', 'operador_nombre': 'Téc. FICTICIO', 'calidad': 'adecuada',
        'parametros': {'kvp': 70, 'mas': 8}})
    assert registro.status_code == 200, registro.text
    completa = await c.post(f'{R}/estudios/{estudio_id}/adquisicion/completar', headers=h)
    assert completa.status_code == 200, completa.text
    return completa.json()


async def informar(rx, estudio_id, contenido, validar=True):
    c, h = rx['c'], rx['h']['radiologo']
    borrador = await c.put(f'{R}/estudios/{estudio_id}/informe/borrador', headers=h,
                           json={'contenido': contenido, 'texto_final': None, 'version_edicion': None})
    assert borrador.status_code == 200, borrador.text
    if not validar:
        return borrador.json()
    validado = await c.post(f'{R}/estudios/{estudio_id}/informe/validar', headers=h, json={
        'version_edicion': borrador.json()['informe']['version_edicion'], 'responsable_nombre': 'Dra. Radióloga FICTICIA',
        'registro_profesional': 'MP-0000', 'confirmo': True})
    assert validado.status_code == 200, validado.text
    return validado.json()


async def test_catalogo_ofrece_estudios_configurados_por_region(rx):
    assert len(rx['tipos']) >= 30
    assert {'torax', 'columna', 'extremidad_inferior'} <= {c['codigo'] for c in rx['catalogo']['categorias']}
    rodilla = rx['tipos']['RX_RODILLA']['config']
    assert rodilla['requiere_lateralidad'] and {p['codigo'] for p in rodilla['proyecciones']} >= {'AP', 'LAT'}
    assert not rx['tipos']['RX_TORAX']['config']['requiere_lateralidad']


async def test_caso_1_torax_completo_hasta_informe_validado(rx):
    c, h = rx['c'], rx['h']
    creada = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_TORAX']['id'], 'protocolo': 'PA_LAT', 'indicacion': 'Tos de 3 semanas'}])
    assert creada.status_code == 201, creada.text
    estudio_id = creada.json()['estudios'][0]['estudio_id']

    detalle = (await c.get(f'{R}/estudios/{estudio_id}', headers=h['rayos_x'])).json()
    assert detalle['estudio']['etapa'] == 'pendiente_realizacion'
    assert detalle['estudio']['detalle']['proyecciones_solicitadas'] == ['PA', 'LAT']
    assert detalle['adquisicion'] is None  # lo solicitado no se asume realizado
    assert detalle['permisos']['registrar_adquisicion'] and not detalle['permisos']['validar']

    adquirido = await adquirir(rx, estudio_id, ['PA', 'LAT'])
    assert adquirido['estudio']['etapa'] == 'pendiente_informe'
    assert [i['proyeccion_codigo'] for i in adquirido['imagenes']] == ['PA', 'LAT']

    contenido = {'generales': {'tecnica': 'Proyecciones PA y lateral.', 'indicacion': 'Tos de 3 semanas.',
                               'conclusion': 'Sin evidencia de consolidación.'},
                 'apartados': {'campos_pulmonares': 'Sin opacidades focales.', 'indice_cardiotoracico': 0.45}}
    previa = await c.post(f'{R}/estudios/{estudio_id}/informe/vista-previa', json={'contenido': contenido}, headers=h['radiologo'])
    assert 'HALLAZGOS:' in previa.json()['texto'] and 'Índice cardiotorácico: 0,45' in previa.json()['texto']

    final = await informar(rx, estudio_id, contenido)
    assert final['estudio']['etapa'] == 'validado' and final['informe']['estado'] == 'publicado'
    assert final['informe']['texto'].index('HALLAZGOS:') < final['informe']['texto'].index('CONCLUSIÓN:')
    assert final['informe']['responsable_nombre'] == 'Dra. Radióloga FICTICIA'
    assert any('validado' in e['descripcion'].lower() for e in final['historial'])

    # El medico solicitante lo ve en el historial del paciente y puede abrir el detalle validado.
    historial = (await c.get(f"/consultas/pacientes/{rx['paciente']}/historial", headers=h['medico'])).json()
    assert any(e['estudio_id'] == estudio_id and 'CONCLUSIÓN' in e['descripcion_texto'] for e in historial['estudios_imagen'])
    assert (await c.get(f'{R}/estudios/{estudio_id}', headers=h['medico'])).status_code == 200


async def test_caso_2_rodilla_derecha_lateralidad_y_plantilla_distinta(rx):
    c, h = rx['c'], rx['h']
    rodilla = rx['tipos']['RX_RODILLA']
    sin_lado = await solicitar(rx, [{'tipo_estudio_id': rodilla['id'], 'protocolo': 'AP_LAT'}])
    assert sin_lado.status_code == 400 and 'lateralidad' in sin_lado.json()['detail']
    invalida = await solicitar(rx, [{'tipo_estudio_id': rodilla['id'], 'lateralidad': 'derecha', 'proyecciones': ['WATERS']}])
    assert invalida.status_code == 400

    creada = await solicitar(rx, [{'tipo_estudio_id': rodilla['id'], 'lateralidad': 'derecha', 'protocolo': 'AP_LAT'}])
    estudio_id = creada.json()['estudios'][0]['estudio_id']
    detalle = (await c.get(f'{R}/estudios/{estudio_id}', headers=h['radiologo'])).json()
    assert detalle['estudio']['lateralidad'] == 'derecha'
    claves = {a['clave'] for a in detalle['config']['plantilla']['apartados']}
    assert 'derrame' in claves and 'campos_pulmonares' not in claves

    incompleta = await c.post(f'{R}/estudios/{estudio_id}/adquisicion/completar', headers=h['rayos_x'])
    assert incompleta.status_code == 409 and incompleta.json()['detail']['pendientes']
    await adquirir(rx, estudio_id, ['AP', 'LAT'], lateralidad='derecha')
    ajeno = await c.put(f'{R}/estudios/{estudio_id}/informe/borrador', headers=h['radiologo'],
                        json={'contenido': {'generales': {}, 'apartados': {'campos_pulmonares': 'x'}}, 'texto_final': None, 'version_edicion': None})
    assert ajeno.status_code == 400  # apartado de torax en un estudio de rodilla


async def test_caso_3_columna_lumbar_apartados_e_informe(rx):
    creada = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_COL_LUMBAR']['id'], 'protocolo': 'AP_LAT'}])
    estudio_id = creada.json()['estudios'][0]['estudio_id']
    await adquirir(rx, estudio_id, ['AP', 'LAT'])
    final = await informar(rx, estudio_id, {
        'generales': {'conclusion': 'Espondiloartrosis lumbar leve.'},
        'apartados': {'alineacion': 'Conservada.', 'espacios_discales': 'Disminución L4-L5.', 'angulo_cobb': 8}})
    texto = final['informe']['texto']
    assert 'Espacios intervertebrales: Disminución L4-L5.' in texto and 'Ángulo de Cobb: 8 °' in texto
    assert texto.index('Alineación vertebral') < texto.index('Espacios intervertebrales')  # orden de la plantilla
    assert 'Curvatura' not in texto  # lo no completado no aparece ni se inventa


async def test_caso_4_solicitud_multiple_mantiene_estudios_independientes(rx):
    c, h = rx['c'], rx['h']
    creada = await solicitar(rx, [
        {'tipo_estudio_id': rx['tipos']['RX_TORAX']['id'], 'protocolo': 'PA'},
        {'tipo_estudio_id': rx['tipos']['RX_RODILLA']['id'], 'lateralidad': 'izquierda', 'protocolo': 'AP_LAT'}], prioridad='urgente')
    cuerpo = creada.json()
    assert len(cuerpo['estudios']) == 2
    torax, rodilla = (e['estudio_id'] for e in cuerpo['estudios'])
    await adquirir(rx, torax, ['PA'], imagenes=(30,))
    await informar(rx, torax, {'generales': {'conclusion': 'Normal.'}, 'apartados': {'campos_pulmonares': 'Libres.'}})

    solicitud = (await c.get(f"{R}/solicitudes/{cuerpo['solicitud_id']}", headers=h['rayos_x'])).json()
    etapas = {e['estudio_id']: e['etapa'] for e in solicitud['estudios']}
    assert etapas == {torax: 'validado', rodilla: 'pendiente_realizacion'}
    detalle_rodilla = (await c.get(f'{R}/estudios/{rodilla}', headers=h['rayos_x'])).json()
    assert detalle_rodilla['imagenes'] == [] and detalle_rodilla['informe'] is None

    activos = (await c.get(f'{R}/estudios', headers=h['radiologo'])).json()
    assert rodilla in {e['estudio_id'] for e in activos} and torax not in {e['estudio_id'] for e in activos}
    finalizados = (await c.get(f'{R}/estudios?vista=finalizados', headers=h['rayos_x'])).json()
    assert torax in {e['estudio_id'] for e in finalizados}
    paciente = (await c.get(f"{R}/pacientes/{rx['paciente']}/estudios", headers=h['rayos_x'])).json()
    assert {torax, rodilla} <= {e['estudio_id'] for e in paciente['estudios']}


async def test_caso_5_borrador_retomado_validacion_y_permisos(rx):
    c, h = rx['c'], rx['h']
    creada = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_TORAX']['id'], 'protocolo': 'PA'}])
    estudio_id = creada.json()['estudios'][0]['estudio_id']
    url = f'{R}/estudios/{estudio_id}'

    antes = await c.put(f'{url}/informe/borrador', headers=h['radiologo'], json={'contenido': {'generales': {}, 'apartados': {}}, 'texto_final': None, 'version_edicion': None})
    assert antes.status_code == 409  # sin adquisicion completada no hay informe
    await adquirir(rx, estudio_id, ['PA'], imagenes=(40,))

    # El tecnico y el medico solicitante no redactan ni validan.
    for rol in ('rayos_x', 'medico', 'laboratorio'):
        r = await c.put(f'{url}/informe/borrador', headers=h[rol], json={'contenido': {}, 'texto_final': None, 'version_edicion': None})
        assert r.status_code == 403
        r = await c.post(f'{url}/informe/validar', headers=h[rol], json={'version_edicion': 1, 'responsable_nombre': 'Alguien', 'confirmo': True})
        assert r.status_code == 403
    heredado = await c.post(f'/imagenes/estudios/{estudio_id}/informes/publicar?modalidad=rayos_x', headers=h['rayos_x'])
    assert heredado.status_code == 403  # tampoco por la ruta anterior

    incompleto = await informar(rx, estudio_id, {'generales': {}, 'apartados': {'campos_pulmonares': 'Opacidad basal derecha.'}}, validar=False)
    assert incompleto['estudio']['etapa'] == 'borrador' and incompleto['informe']['version_edicion'] == 1
    assert incompleto['pendientes']['validacion']
    sin_conclusion = await c.post(f'{url}/informe/validar', headers=h['radiologo'], json={'version_edicion': 1, 'responsable_nombre': 'Dra. FICTICIA', 'confirmo': True})
    assert sin_conclusion.status_code == 409 and 'conclusión' in ' '.join(sin_conclusion.json()['detail']['pendientes']).lower()

    retomado = (await c.get(url, headers=h['radiologo'])).json()
    assert retomado['informe']['contenido']['apartados']['campos_pulmonares'] == 'Opacidad basal derecha.'
    contenido = retomado['informe']['contenido'] | {'generales': {'conclusion': 'Opacidad basal derecha a correlacionar.'}}
    obsoleto = await c.put(f'{url}/informe/borrador', headers=h['radiologo'], json={'contenido': contenido, 'texto_final': None, 'version_edicion': 99})
    assert obsoleto.status_code == 409
    guardado = await c.put(f'{url}/informe/borrador', headers=h['radiologo'], json={'contenido': contenido, 'texto_final': None, 'version_edicion': 1})
    assert guardado.json()['informe']['version_edicion'] == 2
    validado = await c.post(f'{url}/informe/validar', headers=h['radiologo'], json={'version_edicion': 2, 'responsable_nombre': 'Dra. FICTICIA', 'confirmo': True})
    assert validado.status_code == 200 and validado.json()['permisos']['agregar_adenda']

    # Validado = inmutable: ni borrador, ni imagenes, ni adquisicion; solo adendas.
    assert (await c.put(f'{url}/informe/borrador', headers=h['radiologo'], json={'contenido': contenido, 'texto_final': None, 'version_edicion': 2})).status_code == 409
    assert (await c.post(f'{url}/imagenes', files=[('archivos', ('n.png', png(99), 'image/png'))], headers=h['rayos_x'])).status_code == 409
    adenda = await c.post(f'{url}/adendas', headers=h['radiologo'], json={'motivo': 'Aclaración', 'texto': 'Se sugiere control en 4 semanas.', 'autor_nombre': 'Dra. FICTICIA'})
    assert adenda.status_code == 200 and adenda.json()['adendas'][0]['texto'].startswith('Se sugiere')
    assert adenda.json()['informe']['texto'] == validado.json()['informe']['texto']
    with pytest.raises(Exception, match='históricas'):
        async with rx['db'].begin_nested():
            await rx['db'].execute(text("UPDATE radiologia_adenda SET texto='otro'"))

    entregado = await c.post(f'{url}/entregar', headers=h['rayos_x'], json={'entregado_a': 'Paciente'})
    assert entregado.json()['estudio']['etapa'] == 'entregado'


async def test_caso_6_imagenes_multiples_vinculo_retiro_y_acceso(rx):
    c, h = rx['c'], rx['h']
    creada = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_MANO']['id'], 'lateralidad': 'izquierda', 'protocolo': 'COMPLETO'}])
    estudio_id = creada.json()['estudios'][0]['estudio_id']
    url = f'{R}/estudios/{estudio_id}'

    archivos = [('archivos', (f'mano{i}.png', png(60 + i), 'image/png')) for i in range(3)]
    subida = await c.post(f'{url}/imagenes', files=archivos, data={'proyecciones': ['PA', 'OBL', '']}, headers=h['rayos_x'])
    assert subida.status_code == 200, subida.text
    imagenes = subida.json()['imagenes']
    assert [i['proyeccion_codigo'] for i in imagenes] == ['PA', 'OBL', None]
    assert subida.json()['estudio']['etapa'] == 'pendiente_realizacion' and subida.json()['estudio']['imagenes'] == 3

    falso = await c.post(f'{url}/imagenes', files=[('archivos', ('falso.png', b'no soy una imagen', 'image/png'))], headers=h['rayos_x'])
    assert falso.status_code == 415  # se valida el contenido real, no la extension
    pdf = await c.post(f'{url}/imagenes', files=[('archivos', ('x.pdf', b'%PDF-1.4 x', 'application/pdf'))], headers=h['rayos_x'])
    assert pdf.status_code == 415
    repetida = await c.post(f'{url}/imagenes', files=[archivos[0]], headers=h['rayos_x'])
    assert repetida.status_code == 400
    assert (await c.post(f'{url}/imagenes', files=[('archivos', ('r.png', png(90), 'image/png'))], headers=h['radiologo'])).status_code == 403

    tercera = imagenes[2]['id']
    asignada = await c.patch(f'{url}/imagenes/{tercera}', json={'proyeccion_codigo': 'LAT'}, headers=h['rayos_x'])
    assert asignada.json()['imagenes'][2]['proyeccion_codigo'] == 'LAT'
    assert (await c.patch(f'{url}/imagenes/{tercera}', json={'proyeccion_codigo': 'WATERS'}, headers=h['rayos_x'])).status_code == 400
    retirada = await c.post(f'{url}/imagenes/{imagenes[1]["id"]}/retirar', json={'motivo': 'Imagen movida'}, headers=h['rayos_x'])
    assert len(retirada.json()['imagenes']) == 2
    assert await rx['db'].scalar(text('SELECT count(*) FROM archivo_imagen WHERE id=:a AND NOT activo AND motivo_retiro IS NOT NULL'), {'a': imagenes[1]['id']}) == 1

    # Acceso a binarios: personal de Rayos X si; medico solo tras validar; otros roles y anonimos no.
    archivo = imagenes[0]['archivo_id']
    assert (await c.get(f'/imagenes/archivos/{archivo}', headers=h['rayos_x'])).content == png(60)
    vista = await c.get(f'/imagenes/archivos/{archivo}/vista', headers=h['radiologo'])
    assert vista.headers['content-type'] == 'image/png', vista.text
    assert (await c.get(f'/imagenes/archivos/{archivo}', headers=h['medico'])).status_code == 403
    assert (await c.get(f'/imagenes/archivos/{archivo}', headers=h['laboratorio'])).status_code == 403
    assert (await c.get(f'/imagenes/archivos/{archivo}')).status_code == 401
    assert (await c.get(url, headers=h['medico'])).status_code == 403
    assert (await c.get(url, headers=h['laboratorio'])).status_code == 403

    # Informe externo: entidad aparte, solo PDF real, siempre con su establecimiento.
    no_pdf = await c.post(f'{url}/informes-externos', files={'archivo': ('i.pdf', png(1), 'application/pdf')}, data={'establecimiento': 'Centro externo'}, headers=h['rayos_x'])
    assert no_pdf.status_code == 415
    externo = await c.post(f'{url}/informes-externos', files={'archivo': ('i.pdf', b'%PDF-1.4 ficticio', 'application/pdf')},
                           data={'establecimiento': 'Centro externo FICTICIO', 'fecha_informe': '2026-11-10'}, headers=h['rayos_x'])
    assert externo.status_code == 200, externo.text
    registro = externo.json()['informes_externos'][0]
    assert registro['establecimiento'] == 'Centro externo FICTICIO' and externo.json()['informe'] is None
    assert (await c.get(f"{R}/informes-externos/{registro['id']}/archivo", headers=h['radiologo'])).content == b'%PDF-1.4 ficticio'
    assert (await c.get(f"{R}/informes-externos/{registro['id']}/archivo", headers=h['medico'])).status_code == 403


async def test_medico_solicita_desde_consulta_y_recepcion_registra_externos(rx):
    c, h = rx['c'], rx['h']
    del_medico = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_TOBILLO']['id'], 'lateralidad': 'derecha', 'protocolo': 'RUTINA'}], rol='medico', medico_solicitante_id=None)
    assert del_medico.status_code == 201
    fila = (await c.get(f"{R}/estudios/{del_medico.json()['estudios'][0]['estudio_id']}", headers=h['rayos_x'])).json()
    assert fila['solicitud']['medico_solicitante'] and fila['solicitud']['procedencia'] == 'este_centro'

    externo = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_PELVIS']['id'], 'protocolo': 'AP'}], procedencia='otro_centro',
                              medico_solicitante_id=None, medico_solicitante_nombre='Dr. Externo FICTICIO', establecimiento_solicitante_nombre='Centro FICTICIO')
    assert externo.status_code == 201
    sin_medico = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_PELVIS']['id'], 'protocolo': 'AP'}], medico_solicitante_id=None)
    assert sin_medico.status_code == 400

    clave = str(uuid4())
    primera = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_PELVIS']['id'], 'protocolo': 'AP'}], clave_idempotencia=clave)
    repetida = await solicitar(rx, [{'tipo_estudio_id': rx['tipos']['RX_PELVIS']['id'], 'protocolo': 'AP'}], clave_idempotencia=clave)
    assert primera.json() == repetida.json()

    no_realizado = await c.post(f"{R}/estudios/{primera.json()['estudios'][0]['estudio_id']}/no-realizado", json={'motivo': 'Paciente no acudió'}, headers=h['rayos_x'])
    assert no_realizado.json()['estudio']['etapa'] == 'no_realizado'
    assert no_realizado.json()['estudio']['detalle']['motivo_no_realizado'] == 'Paciente no acudió'


async def test_recepcion_busca_y_registra_pacientes_y_medicos(rx):
    c, h = rx['c'], rx['h']
    nuevo = await c.post(f'{R}/pacientes', headers=h['rayos_x'], json={
        'nombre_completo': 'Paciente RX FICTICIO', 'fecha_nacimiento': '1990-05-05', 'sexo': 'F', 'sin_documento': True})
    assert nuevo.status_code == 201, nuevo.text
    encontrados = (await c.get(f'{R}/pacientes?termino=Paciente RX FICT', headers=h['rayos_x'])).json()
    assert nuevo.json()['id'] in {p['id'] for p in encontrados}
    assert (await c.post(f'{R}/pacientes', headers=h['rayos_x'], json={'nombre_completo': 'X', 'fecha_nacimiento': '1990-05-05', 'sexo': 'F'})).status_code == 422
    assert (await c.get(f'{R}/medicos?termino=FICT', headers=h['rayos_x'])).status_code == 200
    assert (await c.get(f'{R}/pacientes?termino=Paciente', headers=h['medico'])).status_code == 403


async def test_radiologo_habilita_y_deshabilita_estudios_del_catalogo(rx):
    c, h = rx['c'], rx['h']
    craneo = rx['tipos']['RX_CRANEO']['id']
    assert (await c.patch(f'{R}/catalogo/estudios/{craneo}', json={'activo': False}, headers=h['rayos_x'])).status_code == 403
    assert (await c.patch(f'{R}/catalogo/estudios/{craneo}', json={'activo': False}, headers=h['radiologo'])).json()['activo'] is False
    visibles = {e['codigo'] for e in (await c.get(f'{R}/catalogo', headers=h['rayos_x'])).json()['estudios']}
    assert 'RX_CRANEO' not in visibles
    todos = {e['codigo'] for e in (await c.get(f'{R}/catalogo?todos=true', headers=h['radiologo'])).json()['estudios']}
    assert 'RX_CRANEO' in todos
    deshabilitado = await solicitar(rx, [{'tipo_estudio_id': craneo, 'protocolo': 'RUTINA'}])
    assert deshabilitado.status_code == 400
