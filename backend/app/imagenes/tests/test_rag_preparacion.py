import pytest
import json
import hashlib
from types import SimpleNamespace

from scripts.preparar_rag_torax import validar_snapshot


def test_snapshot_requiere_safetensors_y_no_acepta_codigo_remoto(tmp_path):
    with pytest.raises(ValueError):
        validar_snapshot(tmp_path)
    (tmp_path / 'model.safetensors').write_bytes(b'fixture')
    (tmp_path / 'config.json').write_text('{}')
    (tmp_path / 'tokenizer.json').write_text('{}')
    assert 'model.safetensors' in validar_snapshot(tmp_path)
    (tmp_path / 'remote.py').write_text('unsafe')
    with pytest.raises(ValueError):
        validar_snapshot(tmp_path)


def test_preparacion_reanuda_modelo_sin_redescargar_corpus(tmp_path, monkeypatch):
    import sys
    import httpx
    import huggingface_hub
    import scripts.preparar_rag_torax as script
    carpeta = tmp_path / '.datasets' / 'rag-torax'
    carpeta.mkdir(parents=True)
    xml = b'<article><article-title>Synthetic test fixture</article-title><permissions><license><license-p>Creative Commons Attribution-NonCommercial-ShareAlike 4.0</license-p></license></permissions><body><p>Test text only.</p></body></article>'
    (carpeta/'test.xml').write_bytes(xml)
    manifiesto = json.dumps({'fuentes':[dict(id='SYN',archivo='test.xml',sha256=hashlib.sha256(xml).hexdigest(),url='synthetic:test',categoria='test',extractor_version='1')]})
    (carpeta/'manifest.json').write_text(manifiesto)
    monkeypatch.setattr(script, 'BASE', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['preparar_rag_torax','--descargar'])
    def prohibir_http(*args, **kwargs):
        pytest.fail('No debe redescargar documentos ya preparados')
    monkeypatch.setattr(httpx, 'Client', prohibir_http)
    monkeypatch.setattr(huggingface_hub, 'HfApi', lambda: SimpleNamespace(model_info=lambda _: SimpleNamespace(sha='test-revision')))
    def snapshot(*args, local_dir, **kwargs):
        local_dir.mkdir(parents=True)
        for nombre in ('model.safetensors','config.json','tokenizer.json'):
            (local_dir/nombre).write_bytes(b'fixture-no-real-model')
    monkeypatch.setattr(huggingface_hub, 'snapshot_download', snapshot)
    script.main()
    assert (tmp_path/'.models/rag-torax/manifest.json').is_file()
    assert (carpeta/'manifest.json').read_text() == manifiesto
