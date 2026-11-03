import pytest

from app.main import app
from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.imagenes.presentation.router import get_repository


@pytest.mark.asyncio
async def test_imagenes_requiere_sesion(client):
    assert (await client.get('/imagenes/estudios')).status_code == 401


@pytest.mark.asyncio
async def test_imagenes_deniega_rol_no_medico(client):
    app.dependency_overrides[usuario_actual] = lambda: Usuario(9,'ficticio','laboratorio',True)
    try:
        assert (await client.get('/imagenes/estudios')).status_code == 403
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
        r = await client.get('/imagenes/estudios/1')
        assert r.status_code == 200
        assert 'url_archivo' not in r.json()['archivo']
        assert (await client.get('/imagenes/estudios/99')).status_code == 404
        assert (await client.post('/imagenes/estudios/1/analisis',json={'confirmar_torax_frontal':False,'proyeccion':'PA','clave':'test'})).status_code == 422
    finally:
        app.dependency_overrides.clear()
