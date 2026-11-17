import pytest

from app.main import app
from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.imagenes.presentation.router_analisis import get_repository


@pytest.mark.asyncio
async def test_imagenes_requiere_sesion(client):
    assert (await client.get('/imagenes/analisis/estudios')).status_code == 401


@pytest.mark.asyncio
async def test_imagenes_deniega_rol_no_medico(client):
    app.dependency_overrides[usuario_actual] = lambda: Usuario(9,'ficticio','laboratorio',True)
    try:
        assert (await client.get('/imagenes/analisis/estudios')).status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_detalle_no_expone_ruta_y_ajeno_es_404(client):
    class Repo:
        async def obtener(self,id,usuario):
            if id != 1:
                return None
            return {'id':1,'informe_texto':'Ficticio','archivo':{'id':2,'url_archivo':'privado/fixture.png','nombre_original':'fixture.png','mime_type':'image/png','tamano_bytes':10,'hash_sha256':'a'*64,'activo':True}}
    app.dependency_overrides[usuario_actual] = lambda: Usuario(9,'ficticio','medico',True)
    app.dependency_overrides[get_repository] = lambda: Repo()
    try:
        r = await client.get('/imagenes/analisis/estudios/1')
        assert r.status_code == 200
        assert 'url_archivo' not in r.json()['archivo']
        assert (await client.get('/imagenes/analisis/estudios/99')).status_code == 404
        assert (await client.post('/imagenes/analisis/estudios/1/analisis',json={'confirmar_torax_frontal':False,'proyeccion':'PA','clave':'test'})).status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_vista_previa_convierte_paleta_a_png_y_no_filtra_detalles(client, tmp_path, monkeypatch):
    import hashlib
    from io import BytesIO
    Image = pytest.importorskip('PIL.Image')
    np = pytest.importorskip('numpy')
    from app.imagenes.presentation import router_analisis
    salida = BytesIO()
    Image.fromarray(np.tile(np.arange(64, dtype=np.uint8) * 4, (48, 1))).convert('P').save(salida, format='PNG')
    datos = salida.getvalue()
    (tmp_path / 'rx.png').write_bytes(datos)
    archivo = {'id': 2, 'url_archivo': 'rx.png', 'nombre_original': 'rx.png', 'mime_type': 'image/png',
               'tamano_bytes': len(datos), 'hash_sha256': hashlib.sha256(datos).hexdigest(), 'activo': True}

    class Repo:
        async def obtener(self, id, usuario):
            return {'id': 1, 'informe_texto': '', 'archivo': archivo} if id == 1 else None
    monkeypatch.setattr(router_analisis, 'raiz_archivos', lambda: tmp_path)
    app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'medico', True)
    app.dependency_overrides[get_repository] = lambda: Repo()
    try:
        r = await client.get('/imagenes/analisis/estudios/1/archivos/2/vista')
        assert r.status_code == 200 and r.headers['content-type'] == 'image/png'
        assert r.headers['x-content-type-options'] == 'nosniff'
        assert Image.open(BytesIO(r.content)).mode == 'L'
        assert (await client.get('/imagenes/analisis/estudios/1/archivos/3/vista')).status_code == 404
        archivo['hash_sha256'] = '0' * 64
        r = await client.get('/imagenes/analisis/estudios/1/archivos/2/vista')
        assert r.status_code == 409 and 'rx.png' not in r.text and str(tmp_path) not in r.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_vista_de_archivo_para_rayos_x_con_permisos_y_sin_filtrar_rutas(client, tmp_path, monkeypatch):
    import hashlib
    from datetime import datetime, timezone
    from io import BytesIO
    from types import SimpleNamespace
    Image = pytest.importorskip('PIL.Image')
    np = pytest.importorskip('numpy')
    from app.imagenes.domain.entities import ArchivoImagen
    from app.imagenes.infrastructure import archivos as modulo_archivos
    from app.imagenes.presentation import descargas
    salida = BytesIO()
    Image.fromarray(np.tile(np.arange(64, dtype=np.uint8) * 4, (48, 1))).save(salida, format='PNG')
    datos = salida.getvalue()
    (tmp_path / 'rx.png').write_bytes(datos)
    archivo = ArchivoImagen(5, 'rx.png', 'image/png', len(datos), hashlib.sha256(datos).hexdigest(), datetime.now(timezone.utc), 'rx.png')

    class Repo:
        async def obtener_archivo(self, _):
            return archivo

        async def obtener_estudio_de_archivo(self, _):
            return SimpleNamespace(tipo_estudio_nombre='Radiografía de tórax', estado='resultado_en_preparacion')
    monkeypatch.setattr(modulo_archivos, 'raices_archivos', lambda: [tmp_path])
    app.dependency_overrides[descargas.get_repositorio] = lambda: Repo()
    try:
        app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'rayos_x', True)
        r = await client.get('/imagenes/archivos/5/vista')
        assert r.status_code == 200 and r.headers['content-type'] == 'image/png'
        app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'medico', True)
        assert (await client.get('/imagenes/archivos/5/vista')).status_code == 403  # médico: aún no publicado
        app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'laboratorio', True)
        assert (await client.get('/imagenes/archivos/5/vista')).status_code == 403
        app.dependency_overrides[usuario_actual] = lambda: Usuario(9, 'ficticio', 'rayos_x', True)
        (tmp_path / 'rx.png').write_bytes(b'alterado')
        r = await client.get('/imagenes/archivos/5/vista')
        assert r.status_code == 409 and str(tmp_path) not in r.text and 'rx.png' not in r.text
    finally:
        app.dependency_overrides.clear()
