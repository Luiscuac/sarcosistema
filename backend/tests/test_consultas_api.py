import pytest


@pytest.mark.asyncio
async def test_busqueda_requiere_sesion(client):
    respuesta = await client.get('/consultas/pacientes', params={'buscar': 'Sol'})
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_rol_laboratorio_no_lee_pacientes_ni_consultas(client, usuarios):
    login = await client.post('/accesos/login', json={
        'identificador_acceso': 'laboratorio_prueba', 'password': 'clave-de-prueba',
    })
    assert login.status_code == 200
    headers = {'Authorization': f"Bearer {login.json()['access_token']}"}
    for ruta in ('/consultas/pacientes?buscar=Sol', '/consultas/pacientes/1',
                 '/consultas/pacientes/1/historial', '/consultas/1'):
        respuesta = await client.get(ruta, headers=headers)
        assert respuesta.status_code == 403
