import hashlib

import pytest

from app.imagenes.infrastructure.rag.corpus import fragmentar, verificar_documento
from app.imagenes.infrastructure.rag.corpus import extraer_articulo


def test_fragmentos_conservan_offsets_y_texto_exacto():
    texto = 'Consolidación pulmonar.\n\nEl derrame pleural requiere correlación clínica.'
    fragmentos = fragmentar(texto, max_caracteres=40)
    assert len(fragmentos) >= 2
    for f in fragmentos:
        assert f['texto'] == texto[f['inicio']:f['fin']]
        assert len(f['texto']) <= 40
    assert ''.join(f['texto'] for f in fragmentos) == texto


def test_documento_alterado_se_rechaza(tmp_path):
    archivo = tmp_path / 'fuente.txt'
    archivo.write_bytes(b'contenido alterado')
    with pytest.raises(ValueError, match='integridad'):
        verificar_documento(archivo, hashlib.sha256(b'original').hexdigest())


def test_documento_valido_se_conserva(tmp_path):
    archivo = tmp_path / 'fuente.txt'
    archivo.write_bytes(b'contenido original')
    assert verificar_documento(archivo, hashlib.sha256(archivo.read_bytes()).hexdigest()) == b'contenido original'


@pytest.mark.parametrize('texto', ['', '   '])
def test_no_fragmenta_documentos_vacios(texto):
    with pytest.raises(ValueError):
        fragmentar(texto)


def test_extrae_secciones_sin_referencias_ni_instrucciones_xml():
    xml = b'<article><front><article-meta><title-group><article-title>Medical review</article-title></title-group><permissions><license><license-p>Creative Commons Attribution-NonCommercial-ShareAlike 4.0</license-p></license></permissions></article-meta></front><body><sec><title>Pleural effusion</title><p>Exact <italic>medical</italic> evidence.</p></sec></body><back><ref-list><ref>Not indexed</ref></ref-list></back></article>'
    articulo = extraer_articulo(xml)
    assert articulo['titulo'] == 'Medical review'
    assert articulo['secciones'] == [{'seccion': 'Pleural effusion', 'texto': 'Exact medical evidence.'}]


def test_rechaza_xml_sin_permiso_y_entidades():
    with pytest.raises(ValueError, match='licencia'):
        extraer_articulo(b'<article><body><p>Text</p></body></article>')
    with pytest.raises(ValueError):
        extraer_articulo(b'<!DOCTYPE a [<!ENTITY x "unsafe">]><article>&x;</article>')


@pytest.mark.parametrize('declaracion', ['Creative Commons test fixture', 'Not licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0'])
def test_licencia_ambigua_o_negada_se_rechaza(declaracion):
    xml = f'<article><article-title>Fixture</article-title><permissions><license><license-p>{declaracion}</license-p></license></permissions><body><p>Test only.</p></body></article>'
    with pytest.raises(ValueError, match='licencia'):
        extraer_articulo(xml.encode())
