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
