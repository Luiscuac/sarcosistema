import hashlib

import pytest

from app.imagenes.infrastructure.archivos import leer_archivo_local


def metadata(contenido, ruta='rx.png'):
    return {'url_archivo': ruta, 'tamano_bytes': len(contenido),
            'hash_sha256': hashlib.sha256(contenido).hexdigest(), 'mime_type': 'image/png', 'activo': True}


def test_lee_solo_archivo_local_con_hash_y_tamano(tmp_path):
    datos = b'\x89PNG\r\n\x1a\nfixture'
    (tmp_path/'rx.png').write_bytes(datos)
    assert leer_archivo_local(tmp_path, metadata(datos)) == (datos, 'image/png')


@pytest.mark.parametrize('ruta', ['../fuera.png', 'https://externo.test/rx.png', '/fuera.png', 'C:\\fuera.png'])
def test_rechaza_rutas_externas_o_traversal(tmp_path, ruta):
    with pytest.raises(ValueError):
        leer_archivo_local(tmp_path, metadata(b'x', ruta))


@pytest.mark.parametrize('cambio', [dict(activo=False), dict(hash_sha256='0'*64), dict(tamano_bytes=1), dict(mime_type='text/html')])
def test_rechaza_metadatos_incompatibles(tmp_path, cambio):
    datos = b'\x89PNG\r\n\x1a\nfixture'
    (tmp_path/'rx.png').write_bytes(datos)
    with pytest.raises(ValueError):
        leer_archivo_local(tmp_path, metadata(datos) | cambio)


def test_no_lee_enlace_fuera_de_raiz(tmp_path):
    raiz = tmp_path/'raiz'
    raiz.mkdir()
    fuera = tmp_path/'fuera.png'
    fuera.write_bytes(b'x')
    try:
        (raiz/'rx.png').symlink_to(fuera)
    except OSError:
        pytest.skip('Crear symlinks requiere privilegio en este Windows')
    with pytest.raises(ValueError):
        leer_archivo_local(raiz, metadata(b'x'))
