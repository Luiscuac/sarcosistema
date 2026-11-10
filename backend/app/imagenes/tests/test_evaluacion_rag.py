import pytest


def test_metricas_retrieval_y_citas_no_confunden_documento_con_seccion():
    from scripts.evaluacion_radiologia.rag import medir_recuperacion, verificar_cita
    q = {'respondible': True, 'referencias': [{'documento_id': 'D', 'seccion': 'S', 'cita': 'abc'}]}
    assert medir_recuperacion(q, [{'documento_id': 'D', 'seccion': 'otra'}]) == {'recall_4': 0, 'mrr': 0}
    assert medir_recuperacion(q, [{'documento_id': 'D', 'seccion': 'otra'}, {'documento_id': 'D', 'seccion': 'S'}]) == {'recall_4': 1, 'mrr': .5}
    assert medir_recuperacion({'respondible': False, 'referencias': []}, [])['recall_4'] is None
    d = {'D': {'contenido': 'abcde', 'sha256': 'hash'}}
    c = {'documento_id': 'D', 'sha256': 'hash', 'inicio': 0, 'fin': 3, 'cita': 'abc'}
    assert verificar_cita(c, d)
    assert not verificar_cita(c | {'cita': 'inventada'}, d)


@pytest.mark.asyncio
async def test_lote_conserva_errores_y_checkpoint_por_pregunta():
    from scripts.evaluacion_radiologia.rag import evaluar_lote
    preguntas = [dict(id=str(i), grupo='fuera_corpus', respondible=False, referencias=[], pregunta='sin tema') for i in range(2)]
    async def buscar(vector):
        if vector == 1:
            raise ConnectionError('detalle no debe filtrarse')
        return []
    checkpoints = []
    filas = await evaluar_lote(preguntas, [0, 1], buscar, {}, lambda filas: checkpoints.append(len(filas)))
    assert checkpoints == [1, 2]
    assert filas[0]['abstiene'] is True
    assert filas[1]['error'] == 'ConnectionError'
    assert 'respuesta' not in filas[1]
