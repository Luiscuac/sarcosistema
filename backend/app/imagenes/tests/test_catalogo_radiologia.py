"""Catalogo de radiologia convencional: consistencia y reglas clinicas basicas."""
import json

from app.imagenes.domain import catalogo_radiologia as cat


def test_catalogo_es_consistente():
    assert cat.validar_catalogo() == []


def test_incluye_estudios_del_encargo_sin_duplicar_por_lateralidad_ni_protocolo():
    codigos = set(cat.ESTUDIOS_POR_CODIGO)
    for codigo in ('RX_TORAX', 'RX_COSTILLAS', 'RX_ESTERNON', 'RX_ABDOMEN', 'RX_COL_CERVICAL', 'RX_COL_DORSAL',
                   'RX_COL_LUMBAR', 'RX_COL_LUMBOSACRA', 'RX_SACRO_COCCIX', 'RX_PELVIS', 'RX_CADERA', 'RX_CLAVICULA',
                   'RX_HOMBRO', 'RX_HUMERO', 'RX_CODO', 'RX_ANTEBRAZO', 'RX_MUNECA', 'RX_MANO', 'RX_DEDOS_MANO',
                   'RX_FEMUR', 'RX_RODILLA', 'RX_ROTULA', 'RX_TIBIA_PERONE', 'RX_TOBILLO', 'RX_PIE', 'RX_DEDOS_PIE',
                   'RX_CALCANEO', 'RX_CRANEO', 'RX_HUESOS_NASALES', 'RX_SENOS_PARANASALES', 'RX_HUESOS_FACIALES'):
        assert codigo in codigos
    # Torax PA / AP / PA y lateral son protocolos, no estudios.
    assert {p.codigo for p in cat.ESTUDIOS_POR_CODIGO['RX_TORAX'].protocolos} == {'PA', 'AP', 'PA_LAT'}
    assert not any('DERECH' in c or 'IZQUIERD' in c for c in codigos)


def test_lateralidad_solo_donde_corresponde():
    assert cat.ESTUDIOS_POR_CODIGO['RX_RODILLA'].requiere_lateralidad
    assert cat.ESTUDIOS_POR_CODIGO['RX_CADERA'].permite_bilateral
    assert not cat.ESTUDIOS_POR_CODIGO['RX_TORAX'].requiere_lateralidad
    assert not cat.ESTUDIOS_POR_CODIGO['RX_COL_LUMBAR'].requiere_lateralidad


def test_plantillas_distintas_por_region():
    torax = cat.configuracion_estudio(cat.ESTUDIOS_POR_CODIGO['RX_TORAX'])['plantilla']
    rodilla = cat.configuracion_estudio(cat.ESTUDIOS_POR_CODIGO['RX_RODILLA'])['plantilla']
    lumbar = cat.configuracion_estudio(cat.ESTUDIOS_POR_CODIGO['RX_COL_LUMBAR'])['plantilla']
    claves = lambda p: {c['clave'] for c in p['apartados']}  # noqa: E731
    assert 'campos_pulmonares' in claves(torax) and 'derrame' in claves(rodilla) and 'espacios_discales' in claves(lumbar)
    assert claves(torax) != claves(rodilla) != claves(lumbar)
    assert [c['clave'] for c in torax['generales']] == list(cat.CLAVES_GENERALES)


def test_configuracion_serializable_y_sin_diagnosticos_autocompletados():
    for estudio in cat.ESTUDIOS:
        config = json.loads(json.dumps(cat.configuracion_estudio(estudio)))
        # Las frases son sugerencias insertables; la conclusion nunca trae texto propuesto.
        conclusion = next(c for c in config['plantilla']['generales'] if c['clave'] == 'conclusion')
        assert 'frases' not in conclusion
