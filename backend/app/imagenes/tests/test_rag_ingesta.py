import hashlib
import json

from app.imagenes.infrastructure.rag.ingesta import cargar_corpus


def test_corpus_preparado_produce_fragmentos_con_citas_exactas(tmp_path):
    xml = b'<article><front><article-title>Test synthetic fixture</article-title><permissions><license><license-p>Creative Commons Attribution-NonCommercial-ShareAlike 4.0</license-p></license></permissions></front><body><sec><title>Section</title><p>Fictional integration text, not medical evidence.</p></sec></body></article>'
    (tmp_path/'fixture.xml').write_bytes(xml)
    (tmp_path/'manifest.json').write_text(json.dumps({'fuentes':[dict(id='SYN',archivo='fixture.xml',sha256=hashlib.sha256(xml).hexdigest(),url='synthetic:test',categoria='test',extractor_version='1')]}))
    corpus = cargar_corpus(tmp_path)
    assert len(corpus) == 1
    documento, fragmentos = corpus[0]
    assert documento['titulo'] == 'Test synthetic fixture'
    assert fragmentos[0]['texto'] == documento['contenido'][fragmentos[0]['inicio']:fragmentos[0]['fin']]
