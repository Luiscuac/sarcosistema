"""Reglas puras de radiologia convencional (sin base de datos)."""
import pytest

from app.imagenes.domain import radiologia as r
from app.imagenes.domain.catalogo_radiologia import ESTUDIOS_POR_CODIGO, configuracion_estudio
from app.imagenes.presentation.router_radiologia import permisos


def config(codigo):
    return configuracion_estudio(ESTUDIOS_POR_CODIGO[codigo])


def test_solicitud_toma_proyecciones_del_protocolo_y_ordena_segun_catalogo():
    detalle = r.normalizar_detalle_solicitud(config('RX_TORAX'), {'protocolo': 'PA_LAT'})
    assert detalle['proyecciones_solicitadas'] == ['PA', 'LAT'] and detalle['lateralidad'] is None
    explicito = r.normalizar_detalle_solicitud(config('RX_RODILLA'), {'lateralidad': 'bilateral', 'proyecciones': ['LAT', 'AP', 'LAT']})
    assert explicito['proyecciones_solicitadas'] == ['AP', 'LAT']


def test_solicitud_sin_proyecciones_ni_protocolo_es_valida():
    assert r.normalizar_detalle_solicitud(config('RX_TORAX'), {})['proyecciones_solicitadas'] == []


@pytest.mark.parametrize('codigo,item', [
    ('RX_RODILLA', {'protocolo': 'AP_LAT'}),                                   # falta lateralidad
    ('RX_TORAX', {'protocolo': 'PA', 'lateralidad': 'derecha'}),               # lateralidad donde no aplica
    ('RX_HOMBRO', {'protocolo': 'RUTINA', 'lateralidad': 'bilateral'}),        # bilateral no permitido
    ('RX_TORAX', {'proyecciones': ['MORTAJA']}),                               # proyeccion de otro estudio
    ('RX_TORAX', {'protocolo': 'AP_LAT_L5S1'}),                                # protocolo de otro estudio
])
def test_solicitud_rechaza_combinaciones_invalidas(codigo, item):
    with pytest.raises(r.ReglaRadiologia):
        r.normalizar_detalle_solicitud(config(codigo), item)


def test_adquisicion_parametros_opcionales_y_validados():
    limpio = r.normalizar_adquisicion(config('RX_TORAX'), {'proyecciones_realizadas': ['PA'], 'parametros': {'kvp': 110, 'mas': '', 'equipo': ' Sala 1 '}})
    assert limpio['parametros'] == {'kvp': 110, 'equipo': 'Sala 1'}
    assert r.normalizar_adquisicion(config('RX_TORAX'), {})['parametros'] == {}
    for malo in ({'kvp': 900}, {'kvp': '70'}, {'voltaje': 1}, {'kvp': True}):
        with pytest.raises(r.ReglaRadiologia):
            r.validar_parametros_tecnicos(malo)
    with pytest.raises(r.ReglaRadiologia):
        r.normalizar_adquisicion(config('RX_TORAX'), {'calidad': 'excelente'})


def test_completar_adquisicion_exige_lo_realizado_no_lo_solicitado():
    rodilla = config('RX_RODILLA')
    assert len(r.pendientes_para_completar_adquisicion(rodilla, None, 0)) == 4
    completa = {'proyecciones_realizadas': ['AP'], 'lateralidad_realizada': 'derecha', 'fecha_hora_adquisicion': 'x', 'repeticiones': 0}
    assert r.pendientes_para_completar_adquisicion(rodilla, completa, 1) == []
    # Las repeticiones ya no se piden en la interfaz: un valor guardado no bloquea completar la adquisición.
    assert r.pendientes_para_completar_adquisicion(rodilla, completa | {'repeticiones': 2}, 1) == []


@pytest.mark.parametrize('estado,adquisicion,contenido,entregado,etapa', [
    ('pendiente_muestra', False, False, False, 'pendiente_realizacion'),
    ('pendiente_muestra', True, False, False, 'en_adquisicion'),
    ('resultado_en_preparacion', True, False, False, 'pendiente_informe'),
    ('resultado_en_preparacion', True, True, False, 'borrador'),
    ('publicado', True, True, False, 'validado'),
    ('publicado', True, True, True, 'entregado'),
    ('no_realizado', False, False, False, 'no_realizado'),
    ('invalidado', False, False, False, 'anulado'),
])
def test_etapa_derivada_del_estado_general(estado, adquisicion, contenido, entregado, etapa):
    assert r.etapa_estudio(estado, adquisicion, contenido, entregado) == etapa
    assert etapa in r.ETAPAS


def test_contenido_valida_plantilla_tipos_y_rangos():
    lumbar = config('RX_COL_LUMBAR')
    limpio = r.normalizar_contenido(lumbar, {'generales': {'conclusion': '  Normal. ', 'tecnica': ''}, 'apartados': {'angulo_cobb': 12.5, 'curvatura': None}})
    assert limpio == {'generales': {'conclusion': 'Normal.'}, 'apartados': {'angulo_cobb': 12.5}}
    for malo in ({'apartados': {'campos_pulmonares': 'x'}}, {'apartados': {'angulo_cobb': 500}}, {'apartados': {'angulo_cobb': 'doce'}},
                 {'generales': {'diagnostico': 'x'}}, {'apartados': {'alineacion': 'x' * 5000}}, 'texto'):
        with pytest.raises(r.ReglaRadiologia):
            r.normalizar_contenido(lumbar, malo)
    edad = config('RX_EDAD_OSEA')
    assert r.normalizar_contenido(edad, {'apartados': {'metodo': 'Greulich y Pyle'}})['apartados']['metodo'] == 'Greulich y Pyle'
    with pytest.raises(r.ReglaRadiologia):
        r.normalizar_contenido(edad, {'apartados': {'metodo': 'Inventado'}})


def test_informe_compuesto_ordena_sin_inventar():
    torax = config('RX_TORAX')
    contenido = r.normalizar_contenido(torax, {
        'generales': {'conclusion': 'Sin hallazgos agudos.', 'indicacion': 'Control.', 'recomendaciones': 'Ninguna.'},
        'apartados': {'pleura': 'Senos libres.', 'campos_pulmonares': 'Sin opacidades.'}})
    texto = r.componer_informe(torax, contenido)
    orden = [texto.index(t) for t in ('INDICACIÓN CLÍNICA:', 'HALLAZGOS:', 'Campos pulmonares:', 'Pleuras y senos', 'CONCLUSIÓN:', 'RECOMENDACIONES:')]
    assert orden == sorted(orden)
    assert 'TÉCNICA' not in texto and 'Mediastino' not in texto and 'COMPARACIÓN' not in texto
    assert r.componer_informe(torax, {'generales': {}, 'apartados': {}}) == ''


def test_validar_exige_conclusion_hallazgo_e_imagenes():
    assert len(r.pendientes_para_validar(None, None, 0)) == 3
    listo = {'generales': {'conclusion': 'x'}, 'apartados': {'a': 'b'}}
    assert r.pendientes_para_validar(listo, None, 1) == []
    assert r.pendientes_para_validar(listo, None, 0, externo=True) == []
    assert r.pendientes_para_validar({'generales': {'conclusion': 'x'}, 'apartados': {}}, 'Texto libre revisado', 1) == []


@pytest.mark.parametrize('rol,estado,etapa,esperados', [
    ('rayos_x', 'pendiente_muestra', 'pendiente_realizacion', {'registrar_adquisicion', 'gestionar_imagenes', 'adjuntar_externo', 'marcar_no_realizado'}),
    ('rayos_x', 'resultado_en_preparacion', 'borrador', {'registrar_adquisicion', 'gestionar_imagenes', 'adjuntar_externo', 'redactar_informe', 'validar'}),
    ('rayos_x', 'publicado', 'validado', {'adjuntar_externo', 'entregar', 'agregar_adenda'}),
    ('medico', 'publicado', 'validado', set()),
    ('rayos_x', 'no_realizado', 'no_realizado', set()),
])
def test_permisos_por_rol_y_estado(rol, estado, etapa, esperados):
    concedidos = {k for k, v in permisos(rol, {'estudio': {'estado': estado, 'etapa': etapa}}).items() if v}
    assert concedidos == esperados
    # El personal de Rayos X también redacta y valida (un solo rol a cargo de todo el flujo).
    assert permisos('rayos_x', {'estudio': {'estado': 'resultado_en_preparacion', 'etapa': 'borrador'}})['validar']
