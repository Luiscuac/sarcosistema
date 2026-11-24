"""Comparación con radiografías anteriores del mismo paciente (experimental, no diagnóstico).

Usa el triaje automático que ya se guarda para cada radiografía de tórax: no ejecuta modelos.
Una diferencia solo se señala si supera la tolerancia de re-toma (evolucion_v1.json): el cambio que producen
por sí solos un paciente algo girado, otra distancia u otro brillo. Dentro de la tolerancia se dice
"sin cambio claro", que NO significa "igual": el médico compara las imágenes.
"""
from datetime import datetime
from functools import lru_cache
import json
from pathlib import Path

ARTEFACTO = Path(__file__).resolve().parents[1] / 'infrastructure' / 'vision' / 'evolucion_v1.json'
MAX_ANTERIORES = 5
MAX_CATEGORIAS = 3
ADVERTENCIA = ('Comparación experimental de las señales del asistente, no de la enfermedad. "Sin cambio claro" no '
               'significa igual. Cambios de equipo, proyección (AP/PA) o inspiración también mueven los números.')


@lru_cache(maxsize=1)
def cargar_tolerancias(ruta: str = str(ARTEFACTO)) -> dict:
    datos = json.loads(Path(ruta).read_text(encoding='utf-8'))
    t = datos['tolerancias']
    if not all(0 < t[k] < 1 for k in ('indice', 'patron_tb_v1', 'patron_tb_v2')):
        raise ValueError('Tolerancias de evolución fuera de rango.')
    return t


def _tendencia(antes, ahora, tolerancia):
    if antes is None or ahora is None:
        return None
    diferencia = ahora - antes
    if abs(diferencia) <= tolerancia:
        clave = 'sin_cambio_claro'
    else:
        clave = 'aumenta' if diferencia > 0 else 'disminuye'
    return {'antes': antes, 'ahora': ahora, 'diferencia': diferencia, 'tolerancia': tolerancia, 'tendencia': clave}


def _tolerancia_patron(version, tolerancias):
    return tolerancias.get('patron_tb_v2' if version == 'patron-tb-v2' else 'patron_tb_v1')


def _patron(antes: dict, ahora: dict, tolerancias: dict):
    if antes.get('patron_tb_version') is None or ahora.get('patron_tb_version') is None:
        return None
    if antes['patron_tb_version'] != ahora['patron_tb_version']:
        # v1 (1 modelo) y v2 (7 modelos) no están en la misma escala: solo se informa, no se compara.
        return {'comparable': False, 'antes_aviso': antes.get('patron_tb_nivel') == 'compatible',
                'ahora_aviso': ahora.get('patron_tb_nivel') == 'compatible'}
    antes_aviso = antes.get('patron_tb_nivel') == 'compatible'
    ahora_aviso = ahora.get('patron_tb_nivel') == 'compatible'
    estado = ('sigue' if antes_aviso and ahora_aviso else 'aparece' if ahora_aviso
              else 'desaparece' if antes_aviso else 'sin_aviso')
    valor = _tendencia(antes.get('patron_tb_valor'), ahora.get('patron_tb_valor'),
                       _tolerancia_patron(ahora['patron_tb_version'], tolerancias))
    return {'comparable': True, 'antes_aviso': antes_aviso, 'ahora_aviso': ahora_aviso, 'estado': estado,
            **({'valor': valor} if valor else {})}


def _categorias(antes: dict, ahora: dict, tolerancias: dict) -> list[dict]:
    tol = tolerancias.get('categorias', {})
    cambios = []
    for nombre, actual in (ahora.get('categorias') or {}).items():
        previo = (antes.get('categorias') or {}).get(nombre)
        if previo is None or nombre not in tol:
            continue
        t = _tendencia(previo, actual, tol[nombre])
        # Solo cambios que además cruzan o están por encima del punto de corte del modelo (0,5): ruido bajo no interesa.
        if t['tendencia'] != 'sin_cambio_claro' and max(previo, actual) >= 0.5:
            cambios.append({'name': nombre, **t})
    cambios.sort(key=lambda c: abs(c['diferencia']), reverse=True)
    return cambios[:MAX_CATEGORIAS]


def _dias(antes, ahora):
    try:
        return (ahora - antes).days if isinstance(antes, datetime) and isinstance(ahora, datetime) else None
    except TypeError:
        return None


def comparar_evolucion(actual: dict | None, anteriores: list[dict], tolerancias: dict) -> dict:
    """actual / anteriores: estudio_id, referencia, fecha, indice, indice_version, patron_tb_valor, patron_tb_nivel,
    patron_tb_version, calidad, categorias{nombre: score}. `anteriores` de más reciente a más antiguo."""
    anteriores = list(anteriores)[:MAX_ANTERIORES]
    resumen = {'actual': actual, 'anteriores': anteriores, 'comparacion': None, 'advertencia': ADVERTENCIA,
               'motivo': None}
    if actual is None:
        resumen['motivo'] = 'sin_triaje_actual'
        return resumen
    if not anteriores:
        resumen['motivo'] = 'sin_anteriores'
        return resumen
    previo = anteriores[0]
    avisos = []
    if 'revisar' in (previo.get('calidad'), actual.get('calidad')):
        avisos.append('Una de las dos imágenes tiene calidad a revisar: la comparación es menos fiable.')
    indice = None
    if previo.get('indice_version') == actual.get('indice_version'):
        indice = _tendencia(previo.get('indice'), actual.get('indice'), tolerancias['indice'])
    else:
        avisos.append('El índice cambió de versión entre ambas radiografías; no se compara.')
    resumen['comparacion'] = {
        'con_estudio_id': previo['estudio_id'], 'con_referencia': previo.get('referencia'),
        'dias': _dias(previo.get('fecha'), actual.get('fecha')),
        'indice': indice, 'patron_tb': _patron(previo, actual, tolerancias),
        'categorias': _categorias(previo, actual, tolerancias), 'avisos': avisos,
    }
    return resumen


def fila_a_punto(fila: dict) -> dict:
    """Fila del repositorio (resultado del triaje) -> punto de la serie, sin datos del paciente."""
    hallazgos = fila.get('hallazgos') or []
    return {'estudio_id': fila['estudio_id'], 'referencia': fila.get('referencia'), 'fecha': fila.get('fecha'),
            'indice': fila.get('indice'), 'indice_version': fila.get('indice_version'),
            'patron_tb_valor': fila.get('patron_tb_valor'), 'patron_tb_nivel': fila.get('patron_tb_nivel'),
            'patron_tb_version': fila.get('patron_tb_version'), 'calidad': fila.get('calidad'),
            'categorias': {h['name']: h['score'] for h in hallazgos if isinstance(h, dict) and 'name' in h}}
