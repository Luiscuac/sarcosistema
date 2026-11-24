"""Triaje visual automático: resumen, cola y prioridad del trabajo médico."""
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from app.imagenes.application.triaje import nivel_prioridad, resumir_triaje
from app.imagenes.infrastructure.persistence.repositorio_asistente import EstudiosRepository
from app.imagenes.infrastructure.persistence.repositorio_triaje import RepositorioTriajeSql
from app.imagenes.infrastructure.trabajos import ejecutar_trabajo
from app.imagenes.tests.test_estudios_imagenes import estudio_fixture  # noqa: F401  (fixture PostgreSQL)


def test_resumen_toma_el_indice_maximo_y_estado_en_proceso():
    filas = [
        {'estudio_id': 1, 'estado': 'completado', 'indice': 0.2, 'calidad': 'ok', 'contribuciones': [{'name': 'A', 'aporte': 1}]},
        {'estudio_id': 1, 'estado': 'completado', 'indice': 0.7, 'calidad': 'revisar', 'contribuciones': [{'name': 'B', 'aporte': 2}]},
        {'estudio_id': 2, 'estado': 'en_cola', 'indice': None, 'calidad': None, 'contribuciones': None},
        {'estudio_id': 3, 'estado': 'error', 'indice': None, 'calidad': None, 'contribuciones': None},
    ]
    r = resumir_triaje(filas)
    assert r[1] == {'estado': 'completado', 'indice': 0.7, 'calidad': 'revisar',
                    'contribuciones': [{'name': 'B', 'aporte': 2}], 'radiografias': 2, 'patron_tb': None}
    assert r[2]['estado'] == 'en_proceso' and r[3]['estado'] == 'error'


@pytest.mark.parametrize('indice,nivel', [(None, None), (0.9, 'alta'), (0.5, 'media'), (0.1, 'baja')])
def test_nivel_por_umbrales(indice, nivel):
    assert nivel_prioridad(indice, 0.65, 0.28) == nivel


class Sesiones:
    @asynccontextmanager
    async def begin(self):
        yield object()


@pytest.mark.asyncio
async def test_triaje_sanea_errores_y_guarda_resultado():
    guardados = []

    class Repo:
        def __init__(self, _):
            pass

        async def archivo_de_triaje(self, trabajo):
            if trabajo['id'] == 'cambiado':
                raise ValueError('ruta/secreta.png')
            return {'id': 5}

        async def finalizar_triaje(self, *args, liderazgo=None):
            guardados.append(args)

    class Triador:
        async def ejecutar(self, archivo):
            if archivo['id'] == 5 and guardados:
                raise RuntimeError('detalle interno C:/secreto')
            return {'tipo': 'triaje', 'indice_pulmonar': {'valor': 0.4}}
    await ejecutar_trabajo({'id': 'ok', 'tipo': 'triaje'}, Sesiones(), None, Repo, triador=Triador())
    await ejecutar_trabajo({'id': 'cambiado', 'tipo': 'triaje'}, Sesiones(), None, Repo, triador=Triador())
    await ejecutar_trabajo({'id': 'falla', 'tipo': 'triaje'}, Sesiones(), None, Repo, triador=Triador())
    assert guardados[0] == ('ok', {'tipo': 'triaje', 'indice_pulmonar': {'valor': 0.4}}, None)
    assert guardados[1] == ('cambiado', None, 'archivo_no_disponible')
    assert guardados[2] == ('falla', None, 'fallo_local')


@pytest.mark.asyncio
async def test_cola_postgres_medico_primero_luego_triaje(estudio_fixture):  # noqa: F811
    db, usuario, estudio, informe, archivo = estudio_fixture
    clinico = RepositorioTriajeSql(db)
    entidad = SimpleNamespace(id=archivo, mime_type='image/png', hash_sha256='a' * 64)
    pdf = SimpleNamespace(id=archivo, mime_type='application/pdf', hash_sha256='b' * 64)
    assert await clinico.encolar_triaje(estudio, [entidad, pdf]) == 1
    assert await clinico.encolar_triaje(estudio, [entidad]) == 0  # deduplicado por estudio + hash
    assert (await clinico.triaje_por_estudio([estudio]))[estudio]['estado'] == 'en_proceso'

    repo = EstudiosRepository(db)
    analisis = await repo.crear_analisis(await repo.obtener(estudio, usuario), usuario, 'triaje-orden', 'PA')
    primero = await repo.reclamar()
    assert primero['tipo'] == 'analisis' and primero['id'] == analisis['id']
    segundo = await repo.reclamar()
    assert segundo['tipo'] == 'triaje' and segundo['estudio_id'] == estudio
    assert (await repo.archivo_de_triaje(segundo))['id'] == archivo

    await repo.recuperar_interrumpidos()  # el triaje procesando vuelve a la cola
    tercero = await repo.reclamar()
    assert tercero['tipo'] == 'triaje' and tercero['id'] == segundo['id']
    await repo.finalizar_triaje(tercero['id'], {'indice_pulmonar': {'valor': 0.83, 'contribuciones': [{'name': 'Nodule', 'aporte': 1.2}]},
                                                'calidad': {'estado': 'ok'}}, None)
    resumen = (await clinico.triaje_por_estudio([estudio]))[estudio]
    assert resumen['estado'] == 'completado' and resumen['indice'] == pytest.approx(0.83)
    assert resumen['contribuciones'][0]['name'] == 'Nodule'
