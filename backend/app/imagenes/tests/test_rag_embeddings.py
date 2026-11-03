import pytest
import json

from app.imagenes.infrastructure.rag.embeddings import EmbeddingsLocales, validar_vectores
from app.imagenes.infrastructure.rag.embeddings import MODEL_ID


def test_modelo_ausente_no_descarga(tmp_path):
    with pytest.raises(ValueError, match='preparado'):
        EmbeddingsLocales(tmp_path).codificar(['derrame pleural'])
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('vectores', [[[0.] * 383], [[float('nan')] * 384], [[0.] * 384]])
def test_vectores_invalidos_se_rechazan(vectores):
    with pytest.raises(ValueError):
        validar_vectores(vectores)


def test_vectores_finitos_normalizados():
    vector = [1.] + [0.] * 383
    assert validar_vectores([vector]) == [vector]


def test_manifest_vacio_no_elude_validacion_de_integridad(tmp_path):
    (tmp_path/'manifest.json').write_text(json.dumps({'model':MODEL_ID,'dimension':384,'files':{}}))
    with pytest.raises(ValueError, match='incompleto'):
        EmbeddingsLocales(tmp_path).codificar(['texto'])
