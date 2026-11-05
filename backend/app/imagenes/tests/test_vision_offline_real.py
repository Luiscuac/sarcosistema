"""Optativo: se ejecuta dentro de Docker --network none con pesos/muestras locales."""
import os
from pathlib import Path
import socket

import pytest

from app.imagenes.domain.vision import VisionConfig, ModeloNoPreparado
from app.imagenes.infrastructure.vision.servicio import AnalizadorTorax

pytestmark = pytest.mark.skipif(os.getenv('RUN_XRAY_OFFLINE_TESTS') != '1', reason='Requiere contenedor de prueba aislado sin red')


def test_contenedor_no_tiene_acceso_a_red_externa():
    # Intento real del SO, no mock de socket; no enviar contenido médico.
    with pytest.raises(OSError):
        socket.create_connection(('1.1.1.1', 443), timeout=2)


def test_dos_radiografias_reales_con_pesos_locales_sin_red():
    resultados = []
    for nombre in ('NIH-RX-001.png', 'NIH-RX-002.png'):
        datos = AnalizadorTorax(VisionConfig(Path('/models'), min_free_bytes=1024**3)).analizar(
            (Path('/samples') / nombre).read_bytes(), proyeccion='PA')
        assert datos['calibrated_probability'] is False
        assert len(datos['findings']) == 3
        assert all(0 <= h['score'] <= 1 for h in datos['findings'])
        resultados.append(datos)
    # Solo derivados experimentales de imágenes de investigación, en tmpfs.
    import json
    Path('/tmp/resultados-offline.json').write_text(json.dumps(resultados, indent=2), encoding='utf-8')
    print('XRAY_OFFLINE_RESULTADOS=' + json.dumps(resultados, separators=(',', ':')))


def test_modelo_ausente_falla_claro_sin_descarga(tmp_path):
    with pytest.raises(ModeloNoPreparado):
        AnalizadorTorax(VisionConfig(tmp_path, min_free_bytes=1024**3)).analizar(b'imagen')
    assert list(tmp_path.iterdir()) == []
