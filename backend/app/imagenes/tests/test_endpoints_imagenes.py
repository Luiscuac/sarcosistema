"""Endpoints de examenes complementarios de imagen (solicitud, subida, publicacion)."""
from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

import pytest

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.imagenes.domain.entities import (
    ArchivoImagen,
    EstudioImagenDetalle,
    EstudioImagenPendiente,
    InformeImagen,
)
from app.imagenes.presentation.router_clinico import get_repositorio
from app.main import app

PNG_MINIMO = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00'
    b'\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00'
    b'\x00\x00IEND\xaeB`\x82'
)


@pytest.fixture
def repositorio_imagen(monkeypatch, tmp_path):
    import app.imagenes.presentation.descargas as descargas
    import app.imagenes.presentation.router_clinico as rutas
    from app.imagenes.infrastructure.storage.almacen_local import AlmacenLocal

    class Doble:
        def __init__(self):
            self.solicitudes = []
            self.bandeja = [
                EstudioImagenPendiente(3, 'EST-3', 'IMG-260101-ABC', 1, 'Paciente ficticio',
                                       'Ecografia abdominal', 'sin_prioridad',
                                       'pendiente_muestra', datetime(2026, 1, 1, tzinfo=timezone.utc)),
            ]
            self.informe = None
            self.archivos = {}
            self.estado_estudio = {'estado': 'pendiente_muestra'}

        async def crear_solicitud(self, solicitud, usuario_id):
            self.solicitudes.append((solicitud, usuario_id))
            return 55

        async def listar_catalogo_imagen(self):
            return [{'id': 101, 'codigo': 'ECO_ABDOMINAL', 'nombre': 'Ecografia abdominal'}]

        async def listar_bandeja(self):
            return self.bandeja

        async def obtener_estudio(self, estudio_id):
            if estudio_id != 3:
                return None
            return EstudioImagenDetalle(
                3, 'EST-3', 'IMG-260101-ABC', 'Paciente ficticio', 'Ecografia abdominal',
                self.estado_estudio['estado'], datetime(2026, 1, 1, tzinfo=timezone.utc),
                self.informe,
            )

        async def guardar_informe(self, estudio_id, descripcion, archivos, usuario_id):
            self.informe = InformeImagen(9, estudio_id, 1, descripcion, 'borrador', None, None,
                                         tuple(ArchivoImagen(
                                             i + 100, a['nombre_original'], a['mime_type'],
                                             a['tamano_bytes'], a['hash_sha256'],
                                             datetime(2026, 1, 2, tzinfo=timezone.utc), a['url_archivo'],
                                         ) for i, a in enumerate(archivos)))
            return self.informe, True

        async def publicar_informe(self, estudio_id, usuario_id):
            self.estado_estudio['estado'] = 'publicado'
            self.informe = InformeImagen(9, estudio_id, 1, self.informe.descripcion_texto,
                                         'publicado', None, datetime(2026, 1, 3, tzinfo=timezone.utc),
                                         self.informe.archivos)
            return self.informe

        async def listar_publicados_paciente(self, paciente_id):
            if self.estado_estudio['estado'] != 'publicado':
                return []
            return [_publicado(self.informe)]

        async def obtener_archivo(self, archivo_id):
            return self.archivos.get(archivo_id)

        async def obtener_estudio_de_archivo(self, archivo_id):
            return await self.obtener_estudio(3)

    doble = Doble()
    import app.consultas.presentation.router as rutas_consultas

    for modulo in (rutas, descargas, rutas_consultas):
        monkeypatch.setattr(modulo, 'RepositorioImagenSql', lambda db: doble)
    almacen = AlmacenLocal(str(tmp_path))
    monkeypatch.setattr(rutas, 'AlmacenLocal', lambda *a, **k: almacen)
    monkeypatch.setattr(descargas, 'AlmacenLocal', lambda *a, **k: almacen)
    yield doble


@pytest.fixture
def medico_sesion():
    """Doble de sesion con rol medico (el modulo /consultas ya exige medico)."""
    app.dependency_overrides[usuario_actual] = lambda: Usuario(7, 'medico_prueba', 'medico', True)
    yield
    app.dependency_overrides.pop(usuario_actual, None)


@pytest.fixture
def radiologo_sesion():
    app.dependency_overrides[usuario_actual] = lambda: Usuario(21, 'rad_prueba', 'imagenes', True)
    yield
    app.dependency_overrides.pop(usuario_actual, None)


def _publicado(informe):
    from app.imagenes.domain.entities import EstudioImagenPublicado

    return EstudioImagenPublicado(
        estudio_id=3, referencia_estudio='EST-3', tipo_estudio_nombre='Ecografia abdominal',
        fecha_solicitud=datetime(2026, 1, 1, tzinfo=timezone.utc),
        fecha_publicacion=informe.fecha_hora_publicacion,
        descripcion_texto=informe.descripcion_texto, archivos=informe.archivos,
    )


# ---------- solicitud del medico ----------

@pytest.mark.asyncio
async def test_medico_solicita_ecografia(client, medico_sesion, repositorio_imagen):
    respuesta = await client.post('/consultas/estudios-imagen', json={
        'paciente_id': 1, 'tipo_estudio_ids': [101, 102],
        'medico_solicitante_nombre': '  Dra. Ficticia  ',
        'clave_idempotencia': str(uuid4()),
    })
    assert respuesta.status_code == 201, respuesta.text
    solicitud, usuario_id = repositorio_imagen.solicitudes[0]
    assert solicitud.paciente_id == 1
    assert solicitud.tipo_estudio_ids == (101, 102)
    assert solicitud.medico_solicitante_nombre == 'Dra. Ficticia'
    assert usuario_id == 7
    assert respuesta.json()['estudios'] == [101, 102]


@pytest.mark.asyncio
async def test_publicar_informe_aparece_en_historial_del_paciente(client, repositorio_imagen):
    """El radiologo publica y el medico lo ve en el historial de su paciente."""
    app.dependency_overrides[usuario_actual] = lambda: Usuario(21, 'rad_prueba', 'imagenes', True)
    try:
        await client.post(
            '/imagenes/estudios/3/informes',
            data={'descripcion': 'Informe ficticio'},
            files=[('archivos', ('eco.png', PNG_MINIMO, 'image/png'))],
        )
        publicar = await client.post('/imagenes/estudios/3/informes/publicar')
        assert publicar.status_code == 200, publicar.text

        app.dependency_overrides[usuario_actual] = lambda: Usuario(7, 'medico_prueba', 'medico', True)
        import app.consultas.presentation.router as rutas_consultas

        class HistorialFalso:
            async def ejecutar(self, paciente_id, pagina, limite):
                return {'items': [], 'total': 0, 'pagina': pagina, 'limite': limite}

        original = rutas_consultas.ConsultarHistorial
        rutas_consultas.ConsultarHistorial = lambda repo: HistorialFalso()
        try:
            historial = await client.get('/consultas/pacientes/1/historial')
            assert historial.status_code == 200
            estudios = historial.json()['estudios_imagen']
            assert len(estudios) == 1
            assert estudios[0]['descripcion_texto'] == 'Informe ficticio'
            assert len(estudios[0]['archivos']) == 1
        finally:
            rutas_consultas.ConsultarHistorial = original
    finally:
        app.dependency_overrides.pop(usuario_actual, None)


@pytest.mark.asyncio
async def test_borrador_no_se_publica_en_el_historial(client, repositorio_imagen):
    app.dependency_overrides[usuario_actual] = lambda: Usuario(21, 'rad_prueba', 'imagenes', True)
    try:
        await client.post(
            '/imagenes/estudios/3/informes',
            data={'descripcion': 'Solo borrador'},
            files=[('archivos', ('eco.png', PNG_MINIMO, 'image/png'))],
        )
        app.dependency_overrides[usuario_actual] = lambda: Usuario(7, 'medico_prueba', 'medico', True)
        import app.consultas.presentation.router as rutas_consultas

        class HistorialFalso:
            async def ejecutar(self, paciente_id, pagina, limite):
                return {'items': [], 'total': 0, 'pagina': pagina, 'limite': limite}

        original = rutas_consultas.ConsultarHistorial
        rutas_consultas.ConsultarHistorial = lambda repo: HistorialFalso()
        try:
            historial = await client.get('/consultas/pacientes/1/historial')
            assert historial.json()['estudios_imagen'] == []
        finally:
            rutas_consultas.ConsultarHistorial = original
    finally:
        app.dependency_overrides.pop(usuario_actual, None)


@pytest.mark.asyncio
@pytest.mark.parametrize('cuerpo', [
    {'tipo_estudio_ids': [101], 'medico_solicitante_nombre': '   '},   # sin profesional
    {'tipo_estudio_ids': [101, 101], 'medico_solicitante_nombre': 'Dra.'},  # repetido
], ids=['sin_medico', 'repetido'])
async def test_solicitud_invalida_devuelve_422(client, medico_sesion, repositorio_imagen, cuerpo):
    base = {'paciente_id': 1, 'medico_solicitante_nombre': 'Dra. Ficticia'}
    respuesta = await client.post('/consultas/estudios-imagen', json={**base, **cuerpo})
    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_solicitud_sin_sesion_devuelve_401(client, repositorio_imagen):
    respuesta = await client.post('/consultas/estudios-imagen', json={
        'paciente_id': 1, 'tipo_estudio_ids': [101], 'medico_solicitante_nombre': 'Dra. Ficticia',
    })
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_medico_ve_el_catalogo_de_ecografias(client, medico_sesion, repositorio_imagen):
    catalogo = await client.get('/consultas/catalogo-imagenes')
    assert catalogo.status_code == 200
    assert catalogo.json() == [
        {'id': 101, 'codigo': 'ECO_ABDOMINAL', 'nombre': 'Ecografia abdominal'},
    ]


@pytest.mark.asyncio
async def test_ruta_de_consulta_no_captura_el_catalogo(client, medico_sesion, repositorio_imagen):
    """Regresion: /consultas/{consulta_id} no debe comerse /catalogo-imagenes."""
    respuesta = await client.get('/consultas/catalogo-imagenes')
    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)
    otra = await client.get('/consultas/999999')
    assert otra.status_code == 404


# ---------- bandeja y trabajo del radiologo ----------

@pytest.mark.asyncio
async def test_radiologo_ve_su_bandeja(client, radiologo_sesion, repositorio_imagen):
    bandeja = await client.get('/imagenes/bandeja')
    assert bandeja.status_code == 200
    assert bandeja.json()[0]['tipo_estudio_nombre'] == 'Ecografia abdominal'
    assert bandeja.json()[0]['referencia_solicitud'] == 'IMG-260101-ABC'


@pytest.mark.asyncio
async def test_medico_no_accede_a_la_bandeja_del_radiologo(client, medico_sesion, repositorio_imagen):
    assert (await client.get('/imagenes/bandeja')).status_code == 403


@pytest.mark.asyncio
async def test_la_bandeja_solo_trae_estudios_de_imagen(client, radiologo_sesion, repositorio_imagen):
    """Regresion: los estudios de laboratorio no deben mezclarse con los de imagen."""
    repositorio_imagen.bandeja = [
        EstudioImagenPendiente(10, 'EST-10', 'IMG-260104-ABC', 23, 'Paciente ficticio',
                               'Ecografia abdominal', 'sin_prioridad', 'pendiente_muestra',
                               datetime(2026, 1, 1, tzinfo=timezone.utc)),
    ]
    bandeja = await client.get('/imagenes/bandeja')
    assert bandeja.status_code == 200
    assert len(bandeja.json()) == 1
    assert bandeja.json()[0]['estudio_id'] == 10


@pytest.mark.asyncio
async def test_estudio_inexistente_devuelve_404(client, radiologo_sesion, repositorio_imagen):
    assert (await client.get('/imagenes/estudios/999')).status_code == 404


@pytest.mark.asyncio
async def test_subir_imagenes_guarda_borrador_con_hash(client, radiologo_sesion, repositorio_imagen):
    respuesta = await client.post(
        '/imagenes/estudios/3/informes',
        data={'descripcion': '  Higado de ecogenicidad normal.  '},
        files=[('archivos', ('eco1.png', PNG_MINIMO, 'image/png')),
               ('archivos', ('eco2.png', PNG_MINIMO, 'image/png'))],
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo['estado'] == 'borrador'
    assert cuerpo['numero_version'] == 1
    assert len(cuerpo['archivos']) == 2
    assert cuerpo['archivos'][0]['hash_sha256']
    assert cuerpo['archivos'][0]['tamano_bytes'] == len(PNG_MINIMO)


@pytest.mark.asyncio
async def test_publicar_sin_informe_devuelve_409(client, radiologo_sesion, repositorio_imagen):
    respuesta = await client.post('/imagenes/estudios/3/informes/publicar')
    assert respuesta.status_code == 409


@pytest.mark.asyncio
async def test_formato_no_admitido_devuelve_415(client, radiologo_sesion, repositorio_imagen):
    respuesta = await client.post(
        '/imagenes/estudios/3/informes',
        data={'descripcion': 'Informe'},
        files=[('archivos', ('virus.exe', b'MZ...', 'application/x-msdownload'))],
    )
    assert respuesta.status_code == 415
    assert 'no admitido' in respuesta.json()['detail']


@pytest.mark.asyncio
async def test_archivo_vacio_devuelve_400(client, radiologo_sesion, repositorio_imagen):
    respuesta = await client.post(
        '/imagenes/estudios/3/informes',
        data={'descripcion': 'Informe'},
        files=[('archivos', ('vacio.png', b'', 'image/png'))],
    )
    assert respuesta.status_code == 400


@pytest.mark.asyncio
async def test_informe_sin_texto_ni_archivos_devuelve_400(client, radiologo_sesion, repositorio_imagen):
    respuesta = await client.post('/imagenes/estudios/3/informes', data={'descripcion': '  '})
    assert respuesta.status_code == 400


@pytest.mark.asyncio
async def test_dicom_se_acepta_y_guarda_extension(client, radiologo_sesion, repositorio_imagen):
    respuesta = await client.post(
        '/imagenes/estudios/3/informes',
        data={'descripcion': 'Estudio DICOM ficticio'},
        files=[('archivos', ('estudio.dcm', b'DICM-ficticio', 'application/dicom'))],
    )
    assert respuesta.status_code == 200, respuesta.text
    archivo = respuesta.json()['archivos'][0]
    assert archivo['mime_type'] == 'application/dicom'
    assert archivo['nombre_original'] == 'estudio.dcm'
