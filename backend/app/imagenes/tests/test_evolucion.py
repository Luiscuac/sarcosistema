"""Comparación con radiografías anteriores del mismo paciente (sin torch)."""
from datetime import datetime, timedelta, timezone
import json
import uuid

import pytest
from sqlalchemy import text

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.imagenes.application.evolucion import cargar_tolerancias, comparar_evolucion, fila_a_punto
from app.imagenes.infrastructure.persistence.repository import EstudiosRepository
from app.imagenes.presentation.router_analisis import get_repository
from app.imagenes.tests.test_estudios_imagenes import estudio_fixture  # noqa: F401
from app.main import app

TOL = {'indice': 0.1, 'patron_tb_v1': 0.1, 'patron_tb_v2': 0.1, 'categorias': {'Consolidation': 0.1, 'Effusion': 0.1}}
AHORA = datetime(2026, 11, 21, tzinfo=timezone.utc)


def punto(estudio_id, indice, dias_atras=0, tb=None, tb_valor=0.2, version='patron-tb-v2', calidad='ok', **cat):
    return {'estudio_id': estudio_id, 'referencia': f'RX-{estudio_id}', 'fecha': AHORA - timedelta(days=dias_atras),
            'indice': indice, 'indice_version': 'indice-pulmonar-v1', 'patron_tb_valor': tb_valor, 'patron_tb_nivel': tb,
            'patron_tb_version': version, 'calidad': calidad, 'categorias': cat}


def test_sin_anteriores_o_sin_triaje_no_compara():
    assert comparar_evolucion(punto(1, 0.5), [], TOL)['motivo'] == 'sin_anteriores'
    assert comparar_evolucion(None, [punto(2, 0.5)], TOL)['motivo'] == 'sin_triaje_actual'


def test_cambio_dentro_de_la_tolerancia_es_sin_cambio_claro():
    r = comparar_evolucion(punto(1, 0.55), [punto(2, 0.50, 30)], TOL)['comparacion']
    assert r['indice']['tendencia'] == 'sin_cambio_claro' and r['dias'] == 30 and r['con_estudio_id'] == 2


def test_aumento_y_disminucion_se_comparan_con_la_mas_reciente():
    anteriores = [punto(2, 0.3, 10), punto(3, 0.9, 60)]
    r = comparar_evolucion(punto(1, 0.8), anteriores, TOL)['comparacion']
    assert r['indice']['tendencia'] == 'aumenta' and r['indice']['diferencia'] == pytest.approx(0.5)
    assert comparar_evolucion(punto(1, 0.1), anteriores, TOL)['comparacion']['indice']['tendencia'] == 'disminuye'


@pytest.mark.parametrize('antes,ahora,estado', [(None, 'compatible', 'aparece'), ('compatible', None, 'desaparece'),
                                                 ('compatible', 'compatible', 'sigue'), (None, None, 'sin_aviso')])
def test_aviso_tb_aparece_o_desaparece(antes, ahora, estado):
    r = comparar_evolucion(punto(1, 0.5, tb=ahora), [punto(2, 0.5, 5, tb=antes)], TOL)['comparacion']['patron_tb']
    assert r['comparable'] and r['estado'] == estado


def test_patron_de_otra_version_no_se_compara():
    r = comparar_evolucion(punto(1, 0.5, tb='compatible'), [punto(2, 0.5, 5, version='patron-tb-v1')], TOL)
    assert r['comparacion']['patron_tb'] == {'comparable': False, 'antes_aviso': False, 'ahora_aviso': True}


def test_categorias_solo_cambios_relevantes_y_calidad_avisa():
    actual = punto(1, 0.5, calidad='revisar', Consolidation=0.85, Effusion=0.30)
    previo = punto(2, 0.5, 5, Consolidation=0.40, Effusion=0.10)  # derrame cambia pero siempre bajo el corte
    r = comparar_evolucion(actual, [previo], TOL)['comparacion']
    assert [c['name'] for c in r['categorias']] == ['Consolidation'] and r['categorias'][0]['tendencia'] == 'aumenta'
    assert any('calidad' in a for a in r['avisos'])


def test_artefacto_de_tolerancias_es_coherente():
    t = cargar_tolerancias()
    assert 0 < t['indice'] < 0.5 and 0 < t['patron_tb_v2'] < 0.5
    from app.imagenes.infrastructure.vision.indice import cargar_indice
    assert set(t['categorias']) == set(cargar_indice()['etiquetas'])


def test_fila_a_punto_toma_las_categorias_del_triaje():
    p = fila_a_punto({'estudio_id': 4, 'hallazgos': [{'name': 'Effusion', 'score': 0.7}, 'basura']})
    assert p['categorias'] == {'Effusion': 0.7}


async def _triaje(db, estudio, archivo, sha, indice, tb=None):
    resultado = {'indice_pulmonar': {'valor': indice, 'version': 'indice-pulmonar-v1'},
                 'patron_tb': {'valor': 0.5, 'nivel': tb, 'version': 'patron-tb-v2'},
                 'calidad': {'estado': 'ok'}, 'all_findings': [{'name': 'Consolidation', 'score': indice}]}
    await db.execute(text('''INSERT INTO public.imagen_triaje_ia (id,estudio_id,archivo_id,archivo_sha256,estado,resultado)
        VALUES (CAST(:id AS uuid),:e,:a,:h,'completado',CAST(:r AS jsonb))'''),
        {'id': str(uuid.uuid4()), 'e': estudio, 'a': archivo, 'h': sha, 'r': json.dumps(resultado)})


async def _estudio_previo(db, estudio, usuario, dias, estado='publicado'):
    """Copia del estudio del fixture para el mismo paciente, `dias` antes."""
    base = (await db.execute(text('''SELECT e.paciente_id,e.servicio_id,e.tipo_estudio_id,s.medico_solicitante_id
        FROM public.estudio_solicitado e JOIN public.solicitud s ON s.id=e.solicitud_id WHERE e.id=:id'''), {'id': estudio})).mappings().one()
    ref = 'TEST-RX-' + uuid.uuid4().hex
    sol = await db.scalar(text('''INSERT INTO public.solicitud(referencia,paciente_id,fecha_solicitud,medico_solicitante_id,prioridad)
        VALUES (:r,:p,now() - make_interval(days => :d),:m,'sin_prioridad') RETURNING id'''),
        {'r': ref, 'p': base['paciente_id'], 'd': dias, 'm': base['medico_solicitante_id']})
    e = await db.scalar(text('''INSERT INTO public.estudio_solicitado(referencia,solicitud_id,paciente_id,servicio_id,tipo_estudio_id,estado)
        VALUES (:r,:s,:p,:v,:t,:estado) RETURNING id'''), {'r': ref, 's': sol, 'p': base['paciente_id'], 'v': base['servicio_id'],
                                                           't': base['tipo_estudio_id'], 'estado': estado})
    inf = await db.scalar(text("""INSERT INTO public.informe_imagen(estudio_id,numero_version,descripcion_texto,estado,usuario_publicacion_id,fecha_hora_publicacion)
        VALUES (:e,1,'Simulación previa.','publicado',:u,now()) RETURNING id"""), {'e': e, 'u': usuario})
    sha = uuid.uuid4().hex * 2
    a = await db.scalar(text('''INSERT INTO public.archivo_imagen(informe_id,nombre_original,url_archivo,mime_type,tamano_bytes,hash_sha256,fecha_carga,created_by)
        VALUES (:i,'previa.png','previa.png','image/png',10,:h,now() - make_interval(days => :d),:u) RETURNING id'''),
        {'i': inf, 'h': sha, 'd': dias, 'u': usuario})
    return e, a, sha


@pytest.mark.asyncio
async def test_serie_del_paciente_solo_anteriores_publicados(estudio_fixture):  # noqa: F811
    db, usuario, estudio, _, archivo = estudio_fixture
    await _triaje(db, estudio, archivo, 'a' * 64, 0.8, 'compatible')
    previo, a_previo, sha = await _estudio_previo(db, estudio, usuario, 40)
    await _triaje(db, previo, a_previo, sha, 0.3)
    sin_publicar, a2, sha2 = await _estudio_previo(db, estudio, usuario, 10, estado='resultado_en_preparacion')
    await _triaje(db, sin_publicar, a2, sha2, 0.9)
    filas = await EstudiosRepository(db).serie_triaje_paciente(estudio)
    assert [f['estudio_id'] for f in filas] == [estudio, previo]
    puntos = [fila_a_punto(f) for f in filas]
    r = comparar_evolucion(puntos[0], puntos[1:], TOL)['comparacion']
    assert r['indice']['tendencia'] == 'aumenta' and r['patron_tb']['estado'] == 'aparece' and r['dias'] in (39, 40)


@pytest.mark.asyncio
async def test_endpoint_evolucion_sin_nombres_y_solo_medico(client):
    class Repo:
        async def obtener(self, estudio_id, usuario_id):
            return {'id': estudio_id} if estudio_id == 7 else None

        async def serie_triaje_paciente(self, estudio_id):
            return [{'estudio_id': 7, 'referencia': 'RX-7', 'fecha': AHORA, 'indice': 0.9, 'indice_version': 'indice-pulmonar-v1',
                     'hallazgos': [{'name': 'Consolidation', 'score': 0.9}]},
                    {'estudio_id': 3, 'referencia': 'RX-3', 'fecha': AHORA - timedelta(days=20), 'indice': 0.1,
                     'indice_version': 'indice-pulmonar-v1', 'hallazgos': [{'name': 'Consolidation', 'score': 0.2}]}]
    app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'medico', True)
    app.dependency_overrides[get_repository] = lambda: Repo()
    try:
        r = await client.get('/imagenes/analisis/estudios/7/evolucion')
        assert r.status_code == 200
        c = r.json()
        assert c['comparacion']['indice']['tendencia'] == 'aumenta' and c['actual']['nivel'] == 'alta'
        assert c['comparacion']['categorias'][0]['name'] == 'Consolidation'
        assert 'categorias' not in c['actual'] and 'paciente' not in r.text
        assert (await client.get('/imagenes/analisis/estudios/8/evolucion')).status_code == 404
        app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'laboratorio', True)
        assert (await client.get('/imagenes/analisis/estudios/7/evolucion')).status_code == 403
    finally:
        app.dependency_overrides.clear()
