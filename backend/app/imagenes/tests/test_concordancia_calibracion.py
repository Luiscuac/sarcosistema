"""Lectura del médico, concordancia médico–IA y calibración local de umbrales."""
import pytest

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.imagenes.application.calibracion import auroc, calibrar, calibrar_tb, resumir_concordancia
from app.imagenes.infrastructure.persistence.repository import EstudiosRepository
from app.imagenes.presentation.router_analisis import get_repository
from app.imagenes.tests.test_estudios_imagenes import estudio_fixture  # noqa: F401
from app.main import app


def test_auroc_y_calibracion_requieren_casos_suficientes():
    assert auroc([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]) == 1.0 and auroc([1], [0.5]) is None
    pocos = calibrar([(0.9, True)] * 5 + [(0.1, False)] * 30)
    assert pocos['estado'] == 'insuficiente' and pocos['faltan_anormales'] == 15 and pocos['faltan_normales'] == 0
    casos = [(0.5 + i / 100, True) for i in range(25)] + [(i / 100, False) for i in range(25)]
    r = calibrar(casos)
    assert r['estado'] == 'calibrado' and r['auroc_local'] == 1.0
    assert r['umbral_sugerido_media'] <= r['umbral_sugerido_alta']
    assert r['operacion_media']['sensibilidad'] >= 0.9
    assert 'no se aplican automáticamente' in r['mensaje']


def test_resumen_de_concordancia_solo_agregados():
    filas = [
        {'estado': 'completado', 'decision': 'aceptada_como_propuesta', 'anormal_confirmado': True, 'indice': 0.9, 'discrepancias': 1, 'omisiones': 0, 'coincidencias': 2},
        {'estado': 'completado', 'decision': 'rechazada', 'anormal_confirmado': False, 'indice': 0.2, 'discrepancias': 0, 'omisiones': 2, 'coincidencias': 0},
        {'estado': 'completado', 'decision': None, 'anormal_confirmado': None, 'indice': 0.5, 'discrepancias': 0, 'omisiones': 0, 'coincidencias': 0},
        {'estado': 'error', 'decision': None, 'anormal_confirmado': None, 'indice': None, 'discrepancias': 0, 'omisiones': 0, 'coincidencias': 0},
    ]
    r = resumir_concordancia(filas)
    assert (r['analisis_totales'], r['analisis_completados'], r['analisis_revisados']) == (4, 3, 2)
    assert r['decisiones'] == {'aceptada_como_propuesta': 1, 'corregida': 0, 'rechazada': 1}
    assert r['tasa_aceptacion'] == 0.5 and r['avisos_generados'] == {'discrepancias': 1, 'omisiones': 2, 'coincidencias': 2}
    assert r['revisados_con_avisos'] == 2 and r['revisados_con_avisos_corregidos_o_rechazados'] == 1
    assert r['lecturas_medicas'] == {'anormal': 1, 'normal': 1} and r['calibracion']['estado'] == 'insuficiente'


@pytest.mark.asyncio
async def test_revision_guarda_lectura_medica_y_aparece_en_concordancia(estudio_fixture):  # noqa: F811
    db, usuario, estudio, _, _ = estudio_fixture
    repo = EstudiosRepository(db)
    a = await repo.crear_analisis(await repo.obtener(estudio, usuario), usuario, 'lectura-medica', 'PA')
    await repo.finalizar(a['id'], {'vision': {'indice_pulmonar': {'valor': 0.77},
                                              'patron_tb': {'valor': 0.66, 'version': 'patron-tb-v2'}},
                                   'fusion': {'discrepancias': [{}], 'posibles_omisiones': [{}, {}], 'coincidencias': []}}, None)
    r = await repo.registrar_revision(a['id'], usuario, 0, 'corregida', 'Motivo ficticio', 'Corrección ficticia', True, True)
    assert r['revisiones'][-1]['anormal_confirmado'] is True and r['revisiones'][-1]['tb_confirmada'] is True
    fila = next(f for f in await repo.filas_concordancia() if f['indice'] == pytest.approx(0.77))
    assert fila['decision'] == 'corregida' and fila['anormal_confirmado'] is True and fila['tb_confirmada'] is True
    assert (fila['discrepancias'], fila['omisiones'], fila['coincidencias']) == (1, 2, 0)
    assert fila['patron_tb'] == pytest.approx(0.66) and fila['patron_tb_version'] == 'patron-tb-v2'


@pytest.mark.asyncio
async def test_endpoint_concordancia_para_medico_sin_datos_personales(client):
    class Repo:
        async def filas_concordancia(self):
            return [{'estado': 'completado', 'decision': 'aceptada_como_propuesta', 'anormal_confirmado': True,
                     'indice': 0.8, 'discrepancias': 0, 'omisiones': 1, 'coincidencias': 1}]
    app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'medico', True)
    app.dependency_overrides[get_repository] = lambda: Repo()
    try:
        r = await client.get('/imagenes/analisis/concordancia')
        assert r.status_code == 200
        cuerpo = r.json()
        assert cuerpo['analisis_revisados'] == 1 and set(cuerpo['umbrales_actuales']) >= {'alta', 'media', 'origen'}
        assert set(cuerpo['patron_tb_actual']) >= {'version', 'umbral_actual', 'origen'}
        assert cuerpo['calibracion_tb']['estado'] == 'insuficiente'
        assert not any(k in r.text for k in ('paciente', 'estudio_id', 'usuario_id'))
        app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'laboratorio', True)
        assert (await client.get('/imagenes/analisis/concordancia')).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_calibracion_tb_solo_con_la_version_en_uso_y_casos_suficientes():
    pocos = calibrar_tb([(0.9, True, 'patron-tb-v2')] * 5 + [(0.1, False, 'patron-tb-v2')] * 30, 'patron-tb-v2', 0.6)
    assert pocos['estado'] == 'insuficiente' and pocos['faltan_con_tb'] == 15 and pocos['faltan_sin_tb'] == 0
    casos = ([(0.5 + i / 100, True, 'patron-tb-v2') for i in range(25)] + [(i / 100, False, 'patron-tb-v2') for i in range(25)]
             + [(0.99, False, 'patron-tb-v1')] * 40 + [(None, True, 'patron-tb-v2'), (0.7, None, 'patron-tb-v2')])
    r = calibrar_tb(casos, 'patron-tb-v2', 0.6)
    assert r['estado'] == 'calibrado' and r['casos'] == 50 and r['otras_versiones'] == 40
    assert r['auroc_local'] == 1.0 and r['operacion_sugerida']['especificidad'] >= 0.9
    assert r['operacion_actual']['umbral'] == 0.6
    assert 'RADIOLOGY_TB_UMBRAL_COMPATIBLE' in r['mensaje'] and 'no solo' in r['mensaje']


def test_resumen_cuenta_lecturas_tb_y_calibra_si_se_indica_la_version():
    filas = [{'estado': 'completado', 'decision': 'aceptada_como_propuesta', 'anormal_confirmado': True, 'indice': 0.9,
              'tb_confirmada': True, 'patron_tb': 0.8, 'patron_tb_version': 'patron-tb-v2',
              'discrepancias': 0, 'omisiones': 0, 'coincidencias': 0},
             {'estado': 'completado', 'decision': 'rechazada', 'anormal_confirmado': True, 'indice': 0.7,
              'tb_confirmada': False, 'patron_tb': 0.3, 'patron_tb_version': 'patron-tb-v2',
              'discrepancias': 0, 'omisiones': 0, 'coincidencias': 0}]
    r = resumir_concordancia(filas, {'version': 'patron-tb-v2', 'umbral_actual': 0.6})
    assert r['lecturas_tb'] == {'confirmada': 1, 'descartada': 1}
    assert r['calibracion_tb']['casos'] == 2 and r['calibracion_tb']['estado'] == 'insuficiente'
    assert resumir_concordancia(filas)['calibracion_tb'] is None
