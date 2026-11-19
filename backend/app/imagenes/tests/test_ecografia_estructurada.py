from types import SimpleNamespace

import pytest

from app.imagenes.domain.ecografia import ORGANOS, validar_datos, texto_informe
from app.imagenes.domain.errors import SolicitudInvalida
from app.imagenes.application.use_cases.trabajar_estudio import GuardarInforme
from app.imagenes.domain.entities import ArchivoImagen
from datetime import datetime, timezone


def datos(codigo='ECO_ABDOMINAL'):
    return {'version': 1, 'tipo': codigo, 'fecha_estudio': '2026-11-14', 'establecimiento': 'Centro FICTICIO',
            'zona': 'Zona FICTICIA', 'conclusion': 'Conclusión escrita de prueba.', 'observaciones': '',
            'evaluaciones': {o: 'Descripción FICTICIA, sin interpretación clínica.' for o in ORGANOS[codigo]}}


@pytest.mark.parametrize('codigo', ORGANOS)
def test_cada_tipo_compone_su_informe_sin_generar_hallazgos(codigo):
    d = validar_datos(datos(codigo), codigo, publicar=True)
    t = texto_informe(d)
    assert all(o.upper() in t for o in ORGANOS[codigo])
    assert 'Conclusión escrita de prueba.' in t


def test_borrador_incompleto_no_puede_publicarse():
    d = datos(); d['evaluaciones']['Hígado'] = ''
    assert validar_datos(d, 'ECO_ABDOMINAL')['evaluaciones']['Hígado'] == ''
    with pytest.raises(SolicitudInvalida): validar_datos(d, 'ECO_ABDOMINAL', publicar=True)


def test_rechaza_plantilla_de_otro_estudio_y_campos_inesperados():
    with pytest.raises(SolicitudInvalida): validar_datos(datos(), 'ECO_RENAL')
    d = datos(); d['evaluaciones']['Campo inventado'] = 'Ficticio'
    with pytest.raises(SolicitudInvalida): validar_datos(d, 'ECO_ABDOMINAL')


@pytest.mark.asyncio
async def test_conserva_adjuntos_anteriores_al_guardar_y_rechaza_ids_ajenos():
    a = ArchivoImagen(7, 'anterior.png', 'image/png', 3, 'abc', datetime.now(timezone.utc), 'local.png')
    class Repo:
        async def obtener_estudio(self, _):
            return SimpleNamespace(informe=SimpleNamespace(estado='borrador', archivos=(a,), datos_ecografia=None))
        async def guardar_informe(self, estudio, texto, archivos, actor):
            assert len(archivos) == 1 and archivos[0]['url_archivo'] == 'local.png'
            return None, True
    caso = GuardarInforme(Repo(), None, ('image/png',), 100, 10)
    assert await caso.ejecutar(1, 'Cambio de texto ficticio', [], 2) == (None, True)
    with pytest.raises(SolicitudInvalida):
        await caso.ejecutar(1, 'Ficticio', [], 2, conservar_archivos=[99])


def test_esquema_del_modelo_limita_hallazgos_a_los_organos_del_tipo():
    from app.imagenes.infrastructure.ia.ecografia import esquema_para_organos

    permitidos = ORGANOS['ECO_RENAL']
    esquema = esquema_para_organos(permitidos)
    hallazgo = next(d for d in esquema['$defs'].values() if 'organo' in d.get('properties', {}))
    assert hallazgo['properties']['organo']['enum'] == list(permitidos)


def test_propuestas_ecografia_conserva_cita_literal_y_descarta_organo_ajeno():
    from app.imagenes.infrastructure.ia.ecografia import (
        CapturaInformeEcografia, HallazgoEcografia, propuestas_ecografia,
    )

    transcripcion = 'Riñón derecho sin dilatación. Bazo no evaluado.'
    salida = CapturaInformeEcografia(hallazgos=[
        HallazgoEcografia(organo='Riñón derecho', valor='Riñón derecho sin dilatación',
                          evidencia='Riñón derecho sin dilatación'),
        HallazgoEcografia(organo='Bazo', valor='Bazo no evaluado', evidencia='Bazo no evaluado'),
    ])
    resultado = propuestas_ecografia(salida, transcripcion, ORGANOS['ECO_RENAL'])
    assert resultado['campos_extraidos'][0]['organo'] == 'Riñón derecho'
    assert resultado['campos_extraidos'][0]['evidencia'] == 'Riñón derecho sin dilatación'
    assert len(resultado['campos_extraidos']) == 1
    assert any('no pertenece' in aviso for aviso in resultado['advertencias'])


@pytest.mark.asyncio
async def test_extractor_recibe_plantilla_del_estudio_y_no_procede_si_esta_publicado():
    from types import SimpleNamespace
    from app.imagenes.application.use_cases.extraer_hallazgos_ecografia import ExtraerHallazgosEcografia
    from app.imagenes.domain.errors import InformeYaPublicado

    estudio = SimpleNamespace(tipo_estudio_codigo='ECO_RENAL', informe=None)
    llamadas = []

    class Repo:
        async def obtener_estudio(self, _):
            return estudio

    class Extractor:
        modelo = 'qwen2.5:3b'

        async def extraer(self, texto, organos):
            llamadas.append((texto, organos))
            return {'campos_extraidos': [], 'advertencias': [], 'bloqueada': False}

    resultado = await ExtraerHallazgosEcografia(Repo(), Extractor()).ejecutar(5, 'Descripción ficticia.')
    assert resultado['modelo'] == 'qwen2.5:3b'
    assert llamadas[0][1] == ORGANOS['ECO_RENAL']

    estudio.informe = SimpleNamespace(estado='publicado')
    with pytest.raises(InformeYaPublicado):
        await ExtraerHallazgosEcografia(Repo(), Extractor()).ejecutar(5, 'Descripción ficticia.')


@pytest.mark.asyncio
async def test_adaptador_ecografia_envia_prompt_y_esquema_por_plantilla_a_ollama_local():
    import json
    import httpx
    from app.imagenes.infrastructure.ia.ecografia import OllamaEcografiaExtractor

    async def responder(request):
        body = json.loads(request.content)
        assert body['model'] == 'qwen2.5:3b'
        assert body['format']['$defs']['HallazgoEcografia']['properties']['organo']['enum'] == list(
            ORGANOS['ECO_RENAL']
        )
        assert 'No completes campos ausentes' in body['messages'][0]['content']
        return httpx.Response(200, json={'message': {'content': json.dumps({
            'hallazgos': [{
                'organo': 'Riñón derecho',
                'valor': 'Riñón derecho sin dilatación.',
                'evidencia': 'Riñón derecho sin dilatación.',
                'ambiguo': False,
            }],
            'datos_generales': [],
            'multiples_pacientes': False,
            'identidad_incierta': False,
        })}})

    extractor = OllamaEcografiaExtractor(transport=httpx.MockTransport(responder))
    resultado = await extractor.extraer(
        'Riñón derecho sin dilatación.', ORGANOS['ECO_RENAL']
    )
    assert resultado['campos_extraidos'][0]['organo'] == 'Riñón derecho'
