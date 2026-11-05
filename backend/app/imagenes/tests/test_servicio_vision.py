import os
import multiprocessing
from pathlib import Path
import time

import pytest

from app.imagenes.domain.vision import VisionConfig, ModeloNoPreparado, ImagenNoValida, TiempoAgotado
from app.imagenes.infrastructure.vision.servicio import AnalizadorTorax


def test_servicio_no_descarga_si_falta_modelo(tmp_path):
    with pytest.raises(ModeloNoPreparado):
        AnalizadorTorax(VisionConfig(model_dir=tmp_path)).analizar(b'contenido')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('parametros', [{'proyeccion': 'L'}, {'repeticiones': 0}, {'repeticiones': 20}])
def test_no_analiza_modalidad_o_carga_no_admitida(tmp_path, parametros):
    with pytest.raises(ValueError):
        AnalizadorTorax(VisionConfig(model_dir=tmp_path)).analizar(b'contenido', **parametros)


def test_servicio_rechaza_audio_o_archivo_vacio_antes_de_crear_trabajador(tmp_path):
    with pytest.raises(ImagenNoValida):
        AnalizadorTorax(VisionConfig(model_dir=tmp_path)).analizar(b'')


def _trabajador_lento(conexion, contenido, config, proyeccion, repeticiones):
    time.sleep(30)


def test_timeout_termina_el_proceso_no_solo_la_espera(tmp_path, monkeypatch):
    pytest.importorskip('psutil')
    import app.imagenes.infrastructure.vision.worker as worker
    monkeypatch.setattr(worker, 'ejecutar_worker', _trabajador_lento)
    anteriores = {p.pid for p in multiprocessing.active_children()}
    with pytest.raises(TiempoAgotado):
        AnalizadorTorax(VisionConfig(tmp_path, timeout_seconds=1))._ejecutar(b'prueba', 'PA', 1)
    assert {p.pid for p in multiprocessing.active_children()} <= anteriores


def _trabajador_ignora_sigterm(conexion, contenido, config, proyeccion, repeticiones):
    import signal
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    (config.model_dir / 'worker-listo').write_text(str(os.getpid()))
    time.sleep(30)


@pytest.mark.skipif(os.name != 'posix', reason='SIGTERM ignorado es un caso POSIX; Windows usa TerminateProcess')
def test_timeout_mata_hijo_que_ignora_sigterm(tmp_path, monkeypatch):
    pytest.importorskip('psutil')
    import app.imagenes.infrastructure.vision.worker as worker
    monkeypatch.setattr(worker, 'ejecutar_worker', _trabajador_ignora_sigterm)
    anteriores = {p.pid for p in multiprocessing.active_children()}
    try:
        with pytest.raises(TiempoAgotado):
            AnalizadorTorax(VisionConfig(tmp_path, timeout_seconds=3))._ejecutar(b'prueba', 'PA', 1)
        assert (tmp_path / 'worker-listo').exists(), 'No se llegó a instalar el rechazo de SIGTERM'
        assert {p.pid for p in multiprocessing.active_children()} <= anteriores
    finally:
        # Solo limpiar los hijos de ESTA prueba si la regresión los dejó vivos.
        for proceso in multiprocessing.active_children():
            if proceso.pid not in anteriores:
                proceso.kill()
                proceso.join(timeout=5)


@pytest.mark.skipif(os.getenv('RUN_XRAY_REAL_TESTS') != '1', reason='Requiere pesos y muestras preparados localmente; nunca los descarga')
def test_inferencia_cpu_real_no_es_diagnostico_ni_probabilidad():
    backend = Path(__file__).resolve().parents[3]
    # Perfil de evaluación de muestras 512×512, tras observar ~400 MiB RSS reales.
    config = VisionConfig(model_dir=backend / '.models' / 'radiologia', min_free_bytes=2 * 1024**3)
    imagen = (backend / '.datasets' / 'radiologia' / 'NIH-RX-001.png').read_bytes()
    resultado = AnalizadorTorax(config).analizar(imagen, proyeccion='PA', repeticiones=2)
    assert resultado['experimental'] is True
    assert resultado['calibrated_probability'] is False
    assert resultado['device'] == 'cpu'
    assert {h['name'] for h in resultado['findings']} == {'Consolidation', 'Effusion', 'Cardiomegaly'}
    assert all(0 <= h['score'] <= 1 for h in resultado['findings'])
    assert 'diagnosis' not in resultado
    assert 'probability' not in resultado
    assert resultado['preprocessing']['input_shape'] == [1, 1, 224, 224]
    assert len(resultado['metrics']['inference_seconds']) == 2
    assert resultado['metrics']['worker_peak_rss_bytes_observed'] > 0
