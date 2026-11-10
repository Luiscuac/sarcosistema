"""Regresiones de composición clínica/IA tras integrar ambos módulos."""
import importlib


def test_puertos_clinicos_y_vision_coexisten():
    clinica = importlib.import_module('app.imagenes.application.ports')
    vision = importlib.import_module('app.imagenes.application.ports.vision')
    caso = importlib.import_module('app.imagenes.application.use_cases.analizar_torax')
    assert clinica.RepositorioImagen
    assert vision.VisionTorax
    assert caso


def test_analisis_publico_conserva_snapshot_revisado_sin_ruta_local():
    from app.imagenes.presentation.router_analisis import analisis_publico
    snapshot = dict(id='ficticio', informe_id=1, archivo_id=2,
                    archivo_sha256='a'*64, informe_sha256='b'*64,
                    informe_texto='INFORME FICTICIO', url_archivo='privado.png')
    publico = analisis_publico(snapshot)
    assert publico['informe_id'] == 1
    assert publico['archivo_id'] == 2
    assert publico['informe_texto'] == 'INFORME FICTICIO'
    assert publico['archivo_sha256'] == 'a'*64
    assert publico['informe_sha256'] == 'b'*64
    assert 'url_archivo' not in publico


def test_rutas_clinicas_y_ia_no_se_duplican():
    from app.main import app
    pares = [(m, r.path) for r in app.routes for m in getattr(r, 'methods', ())]
    assert len(pares) == len(set(pares))
    assert ('GET', '/imagenes/bandeja') in pares
    assert ('GET', '/imagenes/analisis/estudios') in pares
    assert ('POST', '/imagenes/estudios/{estudio_id}/informes/publicar') in pares
    assert ('POST', '/imagenes/analisis/{analisis_id}/revision') in pares
