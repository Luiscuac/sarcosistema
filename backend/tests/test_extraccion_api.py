from uuid import uuid4
import pytest

from app.main import app
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.accesos.domain.entities import Usuario
from app.consultas.presentation.router import get_repository, get_extractor
from app.consultas.domain.extraccion import PropuestaClinica, Sugerencia
from app.consultas.application.ports.extractor_clinico import ErrorExtractor
from app.consultas.presentation.schemas import ConsultaNueva


@pytest.fixture
def medico_extractor():
    app.dependency_overrides[usuario_actual] = lambda: Usuario(7, 'doc_ficticio', 'medico', True)
    class Repo:
        async def obtener_paciente(self, id):
            return {'id': 1} if id == 1 else None
    app.dependency_overrides[get_repository] = lambda: Repo()
    app.dependency_overrides[get_extractor] = lambda: object()
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_extraccion_requiere_sesion_y_rol_medico(client, usuarios):
    sin_token = await client.post('/consultas/extraer-datos-clinicos', json={'paciente_id': 1, 'transcripcion': 'Control'})
    assert sin_token.status_code == 401
    app.dependency_overrides[usuario_actual] = lambda: usuarios
    respuesta = await client.post('/consultas/extraer-datos-clinicos', json={'paciente_id': 1, 'transcripcion': 'Control'})
    assert respuesta.status_code == 403


@pytest.mark.asyncio
async def test_extraccion_valida_paciente_y_devuelve_propuesta_sin_guardar(client, medico_extractor):
    class Extractor:
        modelo = 'qwen2.5:3b'
        async def extraer(self, texto):
            return PropuestaClinica(campos=[Sugerencia(campo='motivo_consulta', valor=texto, evidencia=texto)])
    app.dependency_overrides[get_extractor] = lambda: Extractor()
    respuesta = await client.post('/consultas/extraer-datos-clinicos', json={'paciente_id': 1, 'transcripcion': 'Dolor ficticio'})
    assert respuesta.status_code == 200, respuesta.text
    body = respuesta.json()
    assert body['requiere_revision'] is True
    assert body['campos_extraidos'][0]['valor'] == 'Dolor ficticio'
    assert body['modelo'] == 'qwen2.5:3b'
    assert body['propuesta_id']
    assert 'consulta_id' not in body
    assert (await client.post('/consultas/extraer-datos-clinicos', json={'paciente_id': 999, 'transcripcion': 'Control ficticio'})).status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize('texto', ['   ', 'a' * 12001], ids=['vacio', 'excesivo'])
async def test_no_acepta_texto_vacio_o_excesivo(client, medico_extractor, texto):
    respuesta = await client.post('/consultas/extraer-datos-clinicos', json={'paciente_id': 1, 'transcripcion': texto})
    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_error_modelo_es_recuperable_y_no_revela_texto(client, medico_extractor):
    class Extractor:
        modelo = 'qwen2.5:3b'
        async def extraer(self, texto):
            raise ErrorExtractor('detalle del proveedor que no debe mostrarse')
    app.dependency_overrides[get_extractor] = lambda: Extractor()
    respuesta = await client.post('/consultas/extraer-datos-clinicos', json={'paciente_id': 1, 'transcripcion': 'Información ficticia privada'})
    assert respuesta.status_code == 503
    assert 'privada' not in respuesta.text
    assert 'detalle del proveedor' not in respuesta.text


def test_trazabilidad_ia_no_va_dentro_del_contenido_clinico():
    consulta = ConsultaNueva(paciente_id=1, clave_idempotencia=uuid4(), motivo_consulta='Control',
        diagnostico_principal='Ficticio', revision_ia={'propuesta_id': str(uuid4()),
            'modelo': 'qwen2.5:3b', 'campos_aceptados': ['motivo_consulta']})
    assert 'revision_ia' not in consulta.contenido()
