"""Entrada robusta: formatos reales de equipos (paleta, 16 bits, alta resolución, DICOM)."""
from io import BytesIO

import pytest

from app.imagenes.domain.vision import ImagenNoValida

np = pytest.importorskip('numpy')
Image = pytest.importorskip('PIL.Image')

from app.imagenes.infrastructure.vision.preprocesamiento import (  # noqa: E402
    decodificar_radiografia, detectar_formato, vista_previa_png,
)


def png(imagen):
    salida = BytesIO()
    imagen.save(salida, format='PNG')
    return salida.getvalue()


def degradado(ancho=64, alto=48):
    return np.tile(np.linspace(0, 255, ancho, dtype=np.uint8), (alto, 1))


def dicom(fotometria='MONOCHROME2', sintaxis=None, vista='PA', parte='CHEST', modalidad='DX', valores=None):
    pydicom = pytest.importorskip('pydicom')
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid
    valores = np.tile(np.linspace(0, 4000, 64), (64, 1)).astype(np.uint16) if valores is None else valores
    meta = FileMetaDataset()
    meta.TransferSyntaxUID = sintaxis or ExplicitVRLittleEndian
    meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.1.1'
    meta.MediaStorageSOPInstanceUID = generate_uid()
    ds = Dataset()
    ds.file_meta = meta
    ds.Rows, ds.Columns = valores.shape
    ds.SamplesPerPixel, ds.PhotometricInterpretation = 1, fotometria
    ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 16, 12, 11, 0
    ds.Modality, ds.ViewPosition, ds.BodyPartExamined = modalidad, vista, parte
    if sintaxis:
        from pydicom.encaps import encapsulate
        ds.PixelData = encapsulate([b'\xff\xd8\xff\xe0comprimido'])
    else:
        ds.PixelData = valores.tobytes()
    salida = BytesIO()
    ds.save_as(salida, enforce_file_format=True)
    assert pydicom  # importado solo para omitir si falta
    return salida.getvalue()


def test_png_en_paleta_se_convierte_a_gris_real_no_a_indices():
    # Shenzhen (NLM) llega en modo "P": antes se rechazaba en producción.
    gris = Image.fromarray(degradado())
    arreglo, maxval, meta = decodificar_radiografia(png(gris.convert('P')))
    assert meta['original_mode'] == 'P' and maxval == 255
    assert np.allclose(arreglo, degradado(), atol=2)


@pytest.mark.parametrize('modo', ['LA', 'RGBA', 'RGB'])
def test_png_con_alfa_o_color_se_admite_en_gris(modo):
    arreglo, maxval, _ = decodificar_radiografia(png(Image.fromarray(degradado()).convert(modo)))
    assert arreglo.ndim == 2 and maxval == 255 and arreglo.max() > 250


def test_png_gris_16_bits_se_escala_por_profundidad_efectiva():
    valores = np.tile(np.linspace(0, 4000, 64), (48, 1)).astype(np.uint16)
    arreglo, maxval, meta = decodificar_radiografia(png(Image.fromarray(valores)))
    assert maxval == 4095 and meta['bits'] == 12
    assert arreglo.max() == pytest.approx(4000, abs=1)


def test_alta_resolucion_se_reduce_antes_de_pasar_a_flotante():
    # Montgomery mide 4892x4020 (19,7 MP): antes superaba el límite de 16 MP.
    grande = Image.fromarray(np.zeros((4020, 4892), dtype=np.uint8))
    arreglo, _, meta = decodificar_radiografia(png(grande))
    assert meta['original_size'] == [4892, 4020] and meta['reducida_a_trabajo'] is True
    assert max(arreglo.shape) == 2048


def test_bomba_de_descompresion_se_rechaza_por_dimensiones():
    with pytest.raises(ImagenNoValida, match='megapíxeles'):
        decodificar_radiografia(png(Image.new('1', (16000, 4000))))


def test_dicom_monochrome1_se_invierte_y_expone_metadatos():
    datos = dicom('MONOCHROME1', vista='AP', parte='CHEST')
    assert detectar_formato(datos) == 'dicom'
    arreglo, maxval, meta = decodificar_radiografia(datos)
    assert maxval == 255 and meta['format'] == 'DICOM'
    assert meta['dicom'] == {'modality': 'DX', 'view_position': 'AP', 'body_part': 'CHEST',
                             'photometric': 'MONOCHROME1', 'transfer_syntax': '1.2.840.10008.1.2.1'}
    # Valor crudo alto (izquierda→derecha crece) se ve oscuro en MONOCHROME1.
    assert arreglo[0, 0] == pytest.approx(255) and arreglo[0, -1] == pytest.approx(0)


def test_dicom_monochrome2_conserva_orientacion_de_grises():
    arreglo, _, _ = decodificar_radiografia(dicom('MONOCHROME2'))
    assert arreglo[0, 0] == pytest.approx(0) and arreglo[0, -1] == pytest.approx(255)


def test_dicom_jpeg2000_se_decodifica_localmente():
    pytest.importorskip('openjpeg')
    pydicom = pytest.importorskip('pydicom')
    from pydicom.uid import JPEG2000Lossless
    ds = pydicom.dcmread(BytesIO(dicom('MONOCHROME2')))
    ds.compress(JPEG2000Lossless, encoding_plugin='pylibjpeg')
    salida = BytesIO()
    ds.save_as(salida, enforce_file_format=True)
    arreglo, _, meta = decodificar_radiografia(salida.getvalue())
    assert meta['dicom']['transfer_syntax'] == JPEG2000Lossless
    assert arreglo[0, 0] == pytest.approx(0) and arreglo[0, -1] == pytest.approx(255)
    with Image.open(BytesIO(vista_previa_png(salida.getvalue()))) as imagen:
        assert imagen.mode == 'L'


def test_dicom_comprimido_sin_decodificador_o_no_admitido_da_mensaje_claro(monkeypatch):
    pytest.importorskip('pydicom')
    from pydicom.uid import JPEGBaseline8Bit, JPEGLSLossless
    from app.imagenes.infrastructure.vision import preprocesamiento
    with pytest.raises(ImagenNoValida, match='JPEG-LS'):
        decodificar_radiografia(dicom(sintaxis=JPEGLSLossless))
    monkeypatch.setattr(preprocesamiento, '_decodificador_disponible', lambda sintaxis: False)
    with pytest.raises(ImagenNoValida, match='decodificador'):
        decodificar_radiografia(dicom(sintaxis=JPEGBaseline8Bit))


def test_dicom_comprimido_danado_se_rechaza_sin_detalles_internos():
    pytest.importorskip('libjpeg')
    pytest.importorskip('pydicom')
    from pydicom.uid import JPEGBaseline8Bit
    with pytest.raises(ImagenNoValida, match='píxeles DICOM'):
        decodificar_radiografia(dicom(sintaxis=JPEGBaseline8Bit))


def test_dicom_sin_contraste_se_rechaza():
    with pytest.raises(ImagenNoValida, match='contraste'):
        decodificar_radiografia(dicom(valores=np.full((64, 64), 7, dtype=np.uint16)))


def test_vista_previa_es_png_8_bits_para_cualquier_formato():
    for datos in (dicom('MONOCHROME1'), png(Image.fromarray(degradado()).convert('P'))):
        vista = vista_previa_png(datos)
        with Image.open(BytesIO(vista)) as imagen:
            assert imagen.format == 'PNG' and imagen.mode == 'L'


def test_decodificar_no_importa_torch(monkeypatch):
    import builtins
    original = builtins.__import__

    def importar(nombre, *args, **kwargs):
        if nombre.split('.')[0] in ('torch', 'torchxrayvision'):
            pytest.fail('La decodificación y la vista previa no deben cargar Torch')
        return original(nombre, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', importar)
    vista_previa_png(png(Image.fromarray(degradado())))
