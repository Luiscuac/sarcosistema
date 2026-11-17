"""Resultado enriquecido: 18 categorías, índice, control de calidad y mapas de calor (con dobles)."""
import base64
from io import BytesIO

import pytest

from app.imagenes.domain.vision import TARGETS
from app.imagenes.infrastructure.vision.explicacion import evaluar_calidad, region_del_mapa


def test_resultado_enriquecido_ordena_las_18_y_marca_punto_tecnico():
    from app.imagenes.infrastructure.vision.worker import resultado_enriquecido
    scores = {n: i / 20 for i, n in enumerate(TARGETS)}
    r = resultado_enriquecido(scores, list(TARGETS))
    assert len(r['all_findings']) == 18
    assert [h['score'] for h in r['all_findings']] == sorted(scores.values(), reverse=True)
    assert all(h['above_operating_point'] == (h['score'] >= 0.5) for h in r['all_findings'])
    assert 0 <= r['indice_pulmonar']['valor'] <= 1 and r['indice_pulmonar']['version'] == 'indice-pulmonar-v1'


def test_calidad_ok_en_imagen_frontal_adecuada():
    info = {'original_size': [2048, 2048], 'dicom': {'view_position': 'PA', 'body_part': 'CHEST', 'modality': 'DX'}}
    r = evaluar_calidad(info, desviacion=450, fraccion_saturada=0.01, proyeccion='PA')
    assert r['estado'] == 'ok' and r['avisos'] == []


@pytest.mark.parametrize('info,desv,sat,proy,fragmento', [
    ({'original_size': [640, 480]}, 450, 0.0, 'PA', 'Resolución baja'),
    ({'original_size': [2048, 2048]}, 60, 0.0, 'PA', 'Contraste muy bajo'),
    ({'original_size': [2048, 2048]}, 450, 0.6, 'PA', 'saturada'),
    ({'original_size': [2048, 2048], 'dicom': {'view_position': 'LL'}}, 450, 0.0, 'PA', 'lateral'),
    ({'original_size': [2048, 2048], 'dicom': {'view_position': 'AP'}}, 450, 0.0, 'PA', 'no coincide'),
    ({'original_size': [2048, 2048], 'dicom': {'body_part': 'KNEE'}}, 450, 0.0, 'PA', 'KNEE'),
    ({'original_size': [2048, 2048], 'dicom': {'modality': 'CT'}}, 450, 0.0, 'PA', 'CT'),
])
def test_calidad_avisa_problemas_de_entrada(info, desv, sat, proy, fragmento):
    r = evaluar_calidad(info, desv, sat, proy)
    assert r['estado'] == 'revisar' and any(fragmento in a for a in r['avisos'])


def test_region_del_mapa_corresponde_al_recorte_central():
    assert region_del_mapa([2000, 1000]) == {'x': 0.25, 'y': 0.0, 'ancho': 0.5, 'alto': 1.0}
    assert region_del_mapa([1000, 1000]) == {'x': 0.0, 'y': 0.0, 'ancho': 1.0, 'alto': 1.0}


def test_zona_activa_toma_el_componente_del_maximo():
    np = pytest.importorskip('numpy')
    pytest.importorskip('scipy')
    from app.imagenes.infrastructure.vision.explicacion import zona_activa
    mapa = np.zeros((100, 100), dtype=np.float32)
    mapa[10:20, 60:80] = 1.0    # máximo
    mapa[70:90, 5:15] = 0.7     # otro componente, también sobre el umbral
    z = zona_activa(mapa)
    assert (z['x'], z['y'], z['ancho'], z['alto']) == (0.6, 0.1, 0.2, 0.1)
    assert zona_activa(np.zeros((10, 10))) is None


def test_grad_cam_con_modelo_doble_produce_png_224_y_zona():
    torch = pytest.importorskip('torch')
    Image = pytest.importorskip('PIL.Image')
    pytest.importorskip('scipy')
    from app.imagenes.infrastructure.vision.explicacion import mapas_calor

    class Doble(torch.nn.Module):
        def __init__(self):
            super().__init__()
            torch.manual_seed(0)
            self.features = torch.nn.Conv2d(1, 4, kernel_size=32, stride=32)
            self.classifier = torch.nn.Linear(4, 2)

        def forward(self, x):
            f = torch.nn.functional.relu(self.features(x), inplace=True)  # como XRV
            return torch.sigmoid(self.classifier(f.mean(dim=(2, 3))))
    x = torch.zeros(1, 1, 224, 224)
    x[..., 40:90, 140:200] = 1000.0
    r = mapas_calor(Doble().eval(), x, {'a': lambda s: s[0], 'b': lambda s: s[1]})
    assert set(r) == {'a', 'b'}
    for mapa in r.values():
        with Image.open(BytesIO(base64.b64decode(mapa['png_base64']))) as imagen:
            assert imagen.size == (224, 224) and imagen.mode == 'RGBA'
        assert mapa['zona'] is None or 0 <= mapa['zona']['x'] <= 1


def test_aviso_si_casi_no_hay_campos_pulmonares():
    from app.imagenes.infrastructure.vision.explicacion import agregar_aviso_pulmonar
    ok = agregar_aviso_pulmonar({'estado': 'ok', 'avisos': [], 'medidas': {}}, 0.45)
    assert ok['estado'] == 'ok' and ok['medidas']['fraccion_pulmonar'] == 0.45
    mal = agregar_aviso_pulmonar({'estado': 'ok', 'avisos': [], 'medidas': {}}, 0.03)
    assert mal['estado'] == 'revisar' and 'campos pulmonares' in mal['avisos'][0]


def test_mascara_pulmonar_anula_el_mapa_fuera_de_los_pulmones():
    torch = pytest.importorskip('torch')
    np = pytest.importorskip('numpy')
    pytest.importorskip('scipy')
    from app.imagenes.infrastructure.vision.explicacion import mapas_calor

    class Doble(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.features = torch.nn.Conv2d(1, 2, kernel_size=8, stride=8)
            torch.nn.init.constant_(self.features.weight, 0.01)
            self.classifier = torch.nn.Linear(2, 1)

        def forward(self, x):
            f = torch.nn.functional.relu(self.features(x), inplace=True)
            return torch.sigmoid(self.classifier(f.mean(dim=(2, 3))))
    x = torch.full((1, 1, 224, 224), 500.0)
    mascara = np.zeros((224, 224), dtype=np.float32)
    mascara[:, :112] = 1  # solo la mitad izquierda es "pulmón"
    r = mapas_calor(Doble().eval(), x, {'a': lambda s: s[0]}, mascara)['a']
    assert r['zona'] is None or r['zona']['x'] + r['zona']['ancho'] <= 0.5 + 1e-6


def test_segmentacion_ausente_no_bloquea_el_analisis(tmp_path):
    from app.imagenes.infrastructure.vision.segmentacion import cargar_segmentador, segmentacion_preparada
    assert segmentacion_preparada(tmp_path) is False and cargar_segmentador(tmp_path) is None


def test_segmentacion_alterada_falla_integridad(tmp_path):
    pytest.importorskip('safetensors')  # dependencia opcional de radiología
    import json
    from app.imagenes.domain.vision import ErrorVision
    from app.imagenes.infrastructure.vision.segmentacion import ESTRUCTURAS, MANIFIESTO, PESOS, cargar_segmentador
    (tmp_path / PESOS).write_bytes(b'alterado')
    (tmp_path / MANIFIESTO).write_text(json.dumps({'targets': list(ESTRUCTURAS), 'weights_sha256': '0' * 64}))
    with pytest.raises(ErrorVision, match='integridad'):
        cargar_segmentador(tmp_path)
