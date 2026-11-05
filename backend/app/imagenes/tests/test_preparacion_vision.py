from pathlib import Path

import pytest

from scripts.preparar_modelos_radiologia import descargar_archivo


def test_preparacion_no_acepta_descarga_sin_https(tmp_path):
    with pytest.raises(ValueError):
        descargar_archivo('http://no-autorizado.test/modelo', tmp_path / 'peso.pt', 100)
    assert list(tmp_path.iterdir()) == []


def test_no_sobrescribe_un_archivo_existente_en_preparacion(tmp_path):
    destino = tmp_path / 'peso.pt'
    destino.write_bytes(b'original')
    with pytest.raises(FileExistsError):
        descargar_archivo('https://example.invalid/modelo', destino, 100)
    assert destino.read_bytes() == b'original'
