import pytest


def test_seleccion_excluye_duplicados_paciente_y_vistas_no_frontales():
    from scripts.preparar_evaluacion_radiologia import seleccionar
    filas = [dict(id='a', paciente='1', vista='PA', labels=['Cardiomegaly']),
             dict(id='b', paciente='1', vista='PA', labels=['Effusion']),
             dict(id='c', paciente='2', vista='L', labels=['Consolidation']),
             dict(id='d', paciente='3', vista='AP', labels=['No Finding'])]
    resultado = seleccionar(filas, por_grupo=1)
    assert {r['id'] for r in resultado} == {'b', 'd'}


def test_validacion_rechaza_hash_y_desconocidos_no_son_negativos(tmp_path):
    from scripts.evaluacion_radiologia.visual import validar_muestra, etiquetas_binarias
    p = tmp_path / 'a.png'; p.write_bytes(b'no imagen')
    with pytest.raises(ValueError):
        validar_muestra({'filename': 'a.png', 'sha256': 'falso', 'view_from_source': 'PA'}, tmp_path)
    assert etiquetas_binarias(None) == dict.fromkeys(['Consolidation', 'Effusion', 'Cardiomegaly'])
    assert etiquetas_binarias(['Cardiomegaly'])['Cardiomegaly'] == 1


def test_descarga_reintenta_solo_error_transitorio(monkeypatch):
    import io
    from urllib.error import HTTPError
    from scripts import preparar_evaluacion_radiologia as modulo
    intentos = []
    def abrir(*args, **kwargs):
        intentos.append(1)
        if len(intentos) == 1:
            raise HTTPError('https://ejemplo', 500, 'transitorio', {}, None)
        return io.BytesIO(b'datos')
    monkeypatch.setattr(modulo, 'urlopen', abrir)
    assert modulo.leer_url('https://ejemplo', 10) == b'datos'
    assert len(intentos) == 2


def test_denominador_incluye_perdidas_de_descarga():
    from scripts.evaluacion_radiologia.visual import denominadores
    r = denominadores({'samples': [{}, {}], 'errors': [{'id': 'fallida'}]}, [{'result': {}}, {'error': 'timeout'}])
    assert r == {'n_seleccionados': 3, 'n_descargas_fallidas': 1, 'n_disponibles': 2,
                 'n_intentos': 2, 'n_completados': 1, 'n_errores': 1, 'n_perdidas_totales': 2}
