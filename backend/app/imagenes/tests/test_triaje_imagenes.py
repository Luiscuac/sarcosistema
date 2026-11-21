"""Triaje visual automático: resumen, cola (médico primero), bandeja priorizada y subida."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.imagenes.application.triaje import nivel_prioridad, resumir_triaje
from app.imagenes.domain.entities import ArchivoImagen, EstudioImagenDetalle, EstudioImagenPendiente, InformeImagen
from app.imagenes.infrastructure.persistence.repository import EstudiosRepository, RepositorioImagenSql
from app.imagenes.infrastructure.trabajos import ejecutar_trabajo
from app.imagenes.tests.test_estudios_imagenes import estudio_fixture  # noqa: F401  (fixture PostgreSQL)
from app.main import app


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
async def test_cola_postgres_medico_primero_luego_triaje_y_bandeja(estudio_fixture):  # noqa: F811
    db, usuario, estudio, informe, archivo = estudio_fixture
    clinico = RepositorioImagenSql(db)
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


def _pendiente(estudio_id, prioridad='sin_prioridad'):
    return EstudioImagenPendiente(estudio_id=estudio_id, referencia_estudio=f'RX-{estudio_id}', referencia_solicitud='S',
                                  paciente_id=1, paciente_nombre='Paciente ficticio', tipo_estudio_nombre='Radiografía de tórax PA',
                                  prioridad=prioridad, estado='pendiente', fecha_solicitud=datetime.now(timezone.utc))


@pytest.mark.asyncio
async def test_bandeja_rayos_x_expone_triaje_con_nivel(client):
    from app.imagenes.presentation.router_clinico import get_repositorio

    class Repo:
        async def listar_bandeja(self):
            return [_pendiente(1), _pendiente(2)]

        async def triaje_por_estudio(self, ids):
            assert ids == [1, 2]
            return {1: {'estado': 'completado', 'indice': 0.99, 'calidad': 'ok', 'contribuciones': [], 'radiografias': 1}}
    app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'rayos_x', True)
    app.dependency_overrides[get_repositorio] = lambda: Repo()
    try:
        r = await client.get('/imagenes/bandeja?modalidad=rayos_x')
        assert r.status_code == 200
        filas = {f['estudio_id']: f for f in r.json()}
        assert filas[1]['triaje']['nivel'] == 'alta' and filas[1]['triaje']['indice'] == 0.99
        assert filas[2]['triaje'] is None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize('habilitada,esperado', [(True, 1), (False, 0)])
async def test_subida_rayos_x_encola_triaje_solo_si_la_ia_esta_habilitada(client, tmp_path, monkeypatch, habilitada, esperado):
    from app.config.settings import settings
    from app.imagenes.infrastructure.storage.almacen_local import AlmacenLocal
    from app.imagenes.presentation import router_clinico
    monkeypatch.setattr(settings, 'radiology_ai_enabled', habilitada)
    monkeypatch.setattr(router_clinico, 'AlmacenLocal', lambda: AlmacenLocal(str(tmp_path)))
    encolados = []

    class Repo:
        async def obtener_estudio(self, estudio_id):
            return EstudioImagenDetalle(estudio_id, 'RX-1', 'S', 'Paciente ficticio', 'Radiografía de tórax PA',
                                        'pendiente', datetime.now(timezone.utc), None)

        async def guardar_informe(self, estudio_id, texto, archivos, usuario_id):
            entidades = tuple(ArchivoImagen(i + 1, a['nombre_original'], a['mime_type'], a['tamano_bytes'],
                                            a['hash_sha256'], datetime.now(timezone.utc), a['url_archivo'])
                              for i, a in enumerate(archivos))
            return InformeImagen(1, estudio_id, 1, texto, 'borrador', None, None, entidades), True

        async def encolar_triaje(self, estudio_id, archivos):
            encolados.append([a.mime_type for a in archivos])
    app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'rayos_x', True)
    app.dependency_overrides[router_clinico.get_repositorio] = lambda: Repo()
    dicom = b'\x00' * 128 + b'DICM' + b'fixture'
    try:
        r = await client.post('/imagenes/estudios/1/informes?modalidad=rayos_x',
                              files={'archivos': ('torax.dcm', dicom, 'application/octet-stream')})
        assert r.status_code == 200, r.text
        assert r.json()['archivos'][0]['mime_type'] == 'application/dicom'  # firma, no el tipo del navegador
        assert len(encolados) == esperado
    finally:
        app.dependency_overrides.clear()
