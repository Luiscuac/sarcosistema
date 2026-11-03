from io import BytesIO
from pathlib import Path
import json

import pytest

from app.imagenes.domain.vision import VisionConfig, ImagenNoValida, ModeloNoPreparado, ErrorVision, RecursosInsuficientes
from app.imagenes.infrastructure.vision.artefactos import comprobar_artefactos
from app.imagenes.infrastructure.vision.preprocesamiento import preparar_imagen
from app.imagenes.infrastructure.vision.recursos import verificar_memoria, bloqueo_inferencia


def imagen(modo='L', size=(320, 240), formato='PNG'):
    pil = pytest.importorskip('PIL.Image')
    salida = BytesIO()
    pil.new(modo, size, color=0).save(salida, format=formato)
    return salida.getvalue()


def test_modelo_ausente_falla_sin_intentar_descargar(tmp_path):
    with pytest.raises(ModeloNoPreparado, match='preparar'):
        comprobar_artefactos(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_manifest_no_permite_cambiar_etiquetas_silenciosamente(tmp_path):
    (tmp_path / 'manifest.json').write_text(json.dumps({'model': 'otro-modelo'}))
    with pytest.raises(ErrorVision):
        comprobar_artefactos(tmp_path)


def test_pesos_corruptos_fallan_sin_modificarlos(tmp_path):
    import hashlib
    from app.imagenes.domain.vision import MODEL_ID, XRV_VERSION, TARGETS, WEIGHTS_FILE, PREPROCESS_VERSION, SCORE_KIND
    peso = tmp_path / WEIGHTS_FILE
    contenido = b'fixture-solo-para-integridad' * 100
    peso.write_bytes(contenido)
    (tmp_path / 'manifest.json').write_text(json.dumps({
        'model': MODEL_ID, 'xrv_version': XRV_VERSION, 'targets': list(TARGETS),
        'preprocessing': PREPROCESS_VERSION, 'score_kind': SCORE_KIND,
        'op_threshs': [0.1] * len(TARGETS), 'weights_sha256': hashlib.sha256(contenido).hexdigest(),
    }))
    peso.write_bytes(contenido + b'alterado')
    with pytest.raises(ErrorVision, match='integridad'):
        comprobar_artefactos(tmp_path)
    assert peso.read_bytes() == contenido + b'alterado'


@pytest.mark.parametrize('contenido', [b'', b'no es imagen', b'<svg></svg>'])
def test_rechaza_archivo_invalido(contenido):
    with pytest.raises(ImagenNoValida):
        preparar_imagen(contenido)


def test_preprocesamiento_oscuro_8_bits_es_float32_1_1_224_224():
    pytest.importorskip('torchxrayvision')
    import numpy as np
    tensor, info = preparar_imagen(imagen())
    assert tuple(tensor.shape) == (1, 1, 224, 224)
    assert str(tensor.dtype) == 'torch.float32'
    assert float(tensor.min()) == -1024
    assert float(tensor.max()) == -1024
    assert info['original_size'] == [320, 240]
    assert np.isfinite(tensor.numpy()).all()


def test_rechaza_16_bits_sin_normalizacion_conocida():
    with pytest.raises(ImagenNoValida):
        preparar_imagen(imagen(modo='I;16'))


def test_rechaza_rgb_png_16_bits_antes_de_importar_torch(monkeypatch):
    import builtins
    import struct
    import zlib
    from binascii import crc32
    pil = pytest.importorskip('PIL.Image')
    def chunk(tipo, datos):
        return struct.pack('>I', len(datos)) + tipo + datos + struct.pack('>I', crc32(tipo + datos) & 0xffffffff)
    datos = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 32, 32, 16, 2, 0, 0, 0))
    datos += chunk(b'IDAT', zlib.compress((b'\x00' + b'\xff\xff\x00\x00\x00\x00' * 32) * 32)) + chunk(b'IEND', b'')
    assert pil.open(BytesIO(datos)).mode == 'RGB'  # Pillow oculta la profundidad fuente.
    original = builtins.__import__
    def importar(nombre, *args, **kwargs):
        if nombre in ('torch', 'torchxrayvision'):
            pytest.fail('La imagen de 16 bits debe rechazarse antes de cargar el runtime')
        return original(nombre, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', importar)
    with pytest.raises(ImagenNoValida):
        preparar_imagen(datos)


def test_limita_bytes_antes_de_decodificar():
    with pytest.raises(ImagenNoValida):
        preparar_imagen(b'a' * (10 * 1024 * 1024 + 1))


def test_archivo_no_imagen_se_rechaza_aun_sin_dependencias_opcionales(monkeypatch):
    import builtins
    original = builtins.__import__
    def importar(nombre, *args, **kwargs):
        if nombre == 'PIL':
            raise ImportError('Pillow no instalado')
        return original(nombre, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', importar)
    with pytest.raises(ImagenNoValida):
        preparar_imagen(b'no es imagen')


def test_limita_pixeles_antes_de_convertir():
    with pytest.raises(ImagenNoValida):
        preparar_imagen(imagen(size=(5000, 4000)))


def test_memoria_insuficiente_rechaza_sin_cargar_modelo():
    with pytest.raises(RecursosInsuficientes):
        verificar_memoria(4 * 1024**3, disponible=1024**3)


def test_lock_excluye_dos_solicitudes_y_se_libera(tmp_path):
    with bloqueo_inferencia(tmp_path):
        with pytest.raises(ErrorVision):
            with bloqueo_inferencia(tmp_path):
                pytest.fail('No debe haber dos inferencias simultáneas')
    with bloqueo_inferencia(tmp_path):
        pass


@pytest.mark.parametrize('parametro', [{'threads': 0}, {'threads': 20}, {'timeout_seconds': -1}, {'min_free_bytes': -1}])
def test_rechaza_configuracion_invalida(tmp_path, parametro):
    with pytest.raises(ValueError):
        VisionConfig(model_dir=tmp_path, **parametro)
