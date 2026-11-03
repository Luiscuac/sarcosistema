import hashlib

import pytest

from app.imagenes.application.analizar_estudio import AnalizarEstudio, validar_snapshot


def datos():
    texto = 'No se observa derrame pleural.'
    snapshot = dict(id=1,informe_id=2,informe_texto=texto,archivo=dict(id=3,hash_sha256='a'*64))
    trabajo = dict(estudio_id=1,informe_id=2,archivo_id=3,informe_texto=texto,
        informe_sha256=hashlib.sha256(texto.encode()).hexdigest(),archivo_sha256='a'*64,proyeccion='PA')
    return trabajo,snapshot


def test_rechaza_snapshot_obsoleto():
    trabajo,snapshot = datos()
    snapshot['informe_id'] = 99
    with pytest.raises(ValueError, match='cambió'):
        validar_snapshot(trabajo,snapshot)


@pytest.mark.asyncio
async def test_vision_y_rag_secuenciales_y_fallo_rag_no_inventa_fuentes():
    llamadas = []
    class Vision:
        def analizar(self, contenido, proyeccion):
            llamadas.append('vision')
            return {'findings':[{'name':'Effusion','score':0.8}], 'experimental':True}
    class Rag:
        async def consultar(self, pregunta):
            assert llamadas == ['vision']
            llamadas.append('rag')
            raise ValueError('Fixture: corpus ausente')
    trabajo,snapshot = datos()
    analizador = AnalizarEstudio(Vision(), Rag(), lambda archivo: b'fixture')
    r = await analizador.ejecutar(trabajo,snapshot)
    assert llamadas == ['vision','rag']
    assert r['rag']['estado'] == 'no_disponible'
    assert r['rag']['evidencia'] == []
    assert len(r['fusion']['discrepancias']) == 1
    assert r['fusion']['hallazgos_confirmados'] == []
