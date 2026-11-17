"""Reglas puras de radiologia convencional: solicitud, adquisicion, etapas e informe estructurado.

No acceden a la base ni a la red. La configuracion (`config`) es el JSON guardado en
`tipo_estudio.configuracion_radiologia` (ver `catalogo_radiologia.configuracion_estudio`).

El sistema ordena y da formato a lo que escribe el profesional; nunca agrega hallazgos,
diagnosticos ni conclusiones.
"""
from __future__ import annotations

from app.imagenes.domain.errors import SolicitudInvalida

LATERALIDADES = ('derecha', 'izquierda', 'bilateral')
POSICIONES_PACIENTE = ('bipedestacion', 'sedestacion', 'decubito_supino', 'decubito_prono', 'decubito_lateral')
CALIDADES = ('adecuada', 'limitada', 'no_diagnostica')

# Parametros tecnicos opcionales de la adquisicion: clave -> (minimo, maximo).
PARAMETROS_TECNICOS = {
    'kvp': (20, 200),
    'mas': (0.1, 1000),
    'tiempo_ms': (0.1, 10000),
    'indice_exposicion': (0, 100000),
    'indice_desviacion': (-20, 20),
    'dap': (0, 1000000),
    'distancia_cm': (30, 400),
}
MAX_TEXTO_APARTADO = 4000
MAX_TEXTO_FINAL = 20000

ETAPAS = {
    'pendiente_realizacion': 'Pendiente de realización',
    'en_adquisicion': 'En adquisición',
    'pendiente_informe': 'Pendiente de informe',
    'borrador': 'Informe en borrador',
    'validado': 'Validado',
    'entregado': 'Entregado',
    'no_realizado': 'No realizado',
    'anulado': 'Anulado',
}

TITULOS_GENERALES = {
    'tecnica': 'TÉCNICA',
    'indicacion': 'INDICACIÓN CLÍNICA',
    'comparacion': 'COMPARACIÓN',
    'limitaciones': 'LIMITACIONES TÉCNICAS',
    'conclusion': 'CONCLUSIÓN',
    'recomendaciones': 'RECOMENDACIONES',
}


class ReglaRadiologia(SolicitudInvalida):
    """Dato que no cumple las reglas del estudio radiologico."""


def _texto(valor, maximo: int, campo: str) -> str | None:
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ReglaRadiologia(f'{campo}: se esperaba texto')
    limpio = valor.strip()
    if len(limpio) > maximo:
        raise ReglaRadiologia(f'{campo}: supera {maximo} caracteres')
    return limpio or None


def _codigos_proyeccion(config: dict) -> list[str]:
    return [p['codigo'] for p in config.get('proyecciones', [])]


def validar_proyecciones(config: dict, proyecciones, campo: str = 'proyecciones') -> list[str]:
    """Proyecciones sin repetir y permitidas para el estudio; conserva el orden del catalogo."""
    if not isinstance(proyecciones, (list, tuple)):
        raise ReglaRadiologia(f'{campo}: se esperaba una lista')
    permitidas = _codigos_proyeccion(config)
    pedidas = list(dict.fromkeys(proyecciones))
    fuera = [p for p in pedidas if p not in permitidas]
    if fuera:
        raise ReglaRadiologia(f'{campo}: no corresponden a este estudio: {", ".join(map(str, fuera))}')
    return [p for p in permitidas if p in pedidas]


def validar_lateralidad(config: dict, lateralidad, campo: str = 'lateralidad') -> str | None:
    if not config.get('requiere_lateralidad'):
        if lateralidad not in (None, ''):
            raise ReglaRadiologia(f'{campo}: este estudio no lleva lateralidad')
        return None
    if lateralidad not in LATERALIDADES:
        raise ReglaRadiologia(f'{campo}: indica derecha, izquierda o bilateral')
    if lateralidad == 'bilateral' and not config.get('permite_bilateral', True):
        raise ReglaRadiologia(f'{campo}: este estudio se solicita por lado; crea un estudio por cada lado')
    return lateralidad


def normalizar_detalle_solicitud(config: dict, item: dict) -> dict:
    """Valida la configuracion de un estudio dentro de la solicitud.

    item: {lateralidad?, protocolo?, proyecciones?, indicacion?, observaciones?, detalle_region?}
    Si no se indican proyecciones pero si un protocolo, se toman las del protocolo.
    """
    lateralidad = validar_lateralidad(config, item.get('lateralidad'))
    protocolo = item.get('protocolo') or None
    protocolos = {p['codigo']: p for p in config.get('protocolos', [])}
    if protocolo is not None and protocolo not in protocolos:
        raise ReglaRadiologia('protocolo: no corresponde a este estudio')
    proyecciones = item.get('proyecciones') or []
    if not proyecciones and protocolo:
        proyecciones = protocolos[protocolo]['proyecciones']
    proyecciones = validar_proyecciones(config, proyecciones, 'proyecciones solicitadas')
    # Las proyecciones solicitadas son opcionales: el técnico define las que realiza en la adquisición.
    return {
        'lateralidad': lateralidad,
        'protocolo_codigo': protocolo,
        'proyecciones_solicitadas': proyecciones,
        'indicacion_clinica': _texto(item.get('indicacion'), 1000, 'indicación clínica'),
        'observaciones': _texto(item.get('observaciones'), 1000, 'observaciones'),
        'detalle_region': _texto(item.get('detalle_region'), 200, 'detalle de la región'),
    }


def validar_parametros_tecnicos(parametros) -> dict:
    """Parametros de exposicion opcionales: solo claves conocidas y dentro de rango fisico plausible."""
    if parametros in (None, ''):
        return {}
    if not isinstance(parametros, dict):
        raise ReglaRadiologia('parámetros técnicos: formato no válido')
    limpio: dict = {}
    for clave, valor in parametros.items():
        if valor in (None, ''):
            continue
        if clave == 'equipo':
            limpio[clave] = _texto(valor, 120, 'equipo')
            continue
        if clave not in PARAMETROS_TECNICOS:
            raise ReglaRadiologia(f'parámetros técnicos: {clave} no se admite')
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ReglaRadiologia(f'{clave}: se esperaba un número')
        minimo, maximo = PARAMETROS_TECNICOS[clave]
        if not minimo <= valor <= maximo:
            raise ReglaRadiologia(f'{clave}: fuera del rango admitido ({minimo}–{maximo})')
        limpio[clave] = valor
    return {k: v for k, v in limpio.items() if v is not None}


def normalizar_adquisicion(config: dict, datos: dict) -> dict:
    """Valida el registro tecnico. Todo es opcional mientras este en proceso."""
    posicion = datos.get('posicion_paciente') or None
    if posicion is not None and posicion not in POSICIONES_PACIENTE:
        raise ReglaRadiologia('posición del paciente: valor no admitido')
    calidad = datos.get('calidad') or None
    if calidad is not None and calidad not in CALIDADES:
        raise ReglaRadiologia('calidad: valor no admitido')
    repeticiones = datos.get('repeticiones') or 0
    if isinstance(repeticiones, bool) or not isinstance(repeticiones, int) or not 0 <= repeticiones <= 20:
        raise ReglaRadiologia('repeticiones: indica un número entre 0 y 20')
    lateralidad = datos.get('lateralidad_realizada') or None
    if lateralidad is not None:
        lateralidad = validar_lateralidad(config, lateralidad, 'lateralidad realizada')
    return {
        'proyecciones_realizadas': validar_proyecciones(config, datos.get('proyecciones_realizadas') or [], 'proyecciones realizadas'),
        'lateralidad_realizada': lateralidad,
        'posicion_paciente': posicion,
        'calidad': calidad,
        'limitaciones': _texto(datos.get('limitaciones'), 1000, 'limitaciones'),
        'repeticiones': repeticiones,
        'motivo_repeticion': _texto(datos.get('motivo_repeticion'), 500, 'motivo de repetición'),
        'parametros': validar_parametros_tecnicos(datos.get('parametros')),
        'observaciones': _texto(datos.get('observaciones'), 1000, 'observaciones técnicas'),
        'operador_nombre': _texto(datos.get('operador_nombre'), 200, 'operador'),
    }


def pendientes_para_completar_adquisicion(config: dict, adquisicion: dict | None, imagenes: int) -> list[str]:
    """Lo que falta para cerrar la adquisicion (lista vacia = se puede completar)."""
    faltan = []
    if not adquisicion or not adquisicion.get('proyecciones_realizadas'):
        faltan.append('Registra al menos una proyección realizada.')
    if config.get('requiere_lateralidad') and not (adquisicion or {}).get('lateralidad_realizada'):
        faltan.append('Indica la lateralidad realizada.')
    if not (adquisicion or {}).get('fecha_hora_adquisicion'):
        faltan.append('Indica la fecha y hora de adquisición.')
    if imagenes < 1:
        faltan.append('Adjunta al menos una imagen.')
    if (adquisicion or {}).get('repeticiones') and not (adquisicion or {}).get('motivo_repeticion'):
        faltan.append('Indica el motivo de las repeticiones.')
    return faltan


def etapa_estudio(estado: str, tiene_adquisicion: bool, informe_con_contenido: bool, entregado: bool) -> str:
    """Etapa radiologica derivada del estado general del estudio (compartido con Laboratorio)."""
    if estado == 'no_realizado':
        return 'no_realizado'
    if estado == 'invalidado':
        return 'anulado'
    if estado == 'publicado':
        return 'entregado' if entregado else 'validado'
    if estado == 'resultado_en_preparacion':
        return 'borrador' if informe_con_contenido else 'pendiente_informe'
    return 'en_adquisicion' if tiene_adquisicion else 'pendiente_realizacion'


def _plantilla(config: dict) -> dict:
    return config.get('plantilla') or {'generales': [], 'apartados': []}


def normalizar_contenido(config: dict, contenido) -> dict:
    """Valida el contenido estructurado contra la plantilla del estudio.

    contenido: {'generales': {clave: texto}, 'apartados': {clave: texto | numero}}
    Los campos vacios se descartan: nada es obligatorio en borrador.
    """
    if not isinstance(contenido, dict):
        raise ReglaRadiologia('contenido: formato no válido')
    plantilla = _plantilla(config)
    salida = {'generales': {}, 'apartados': {}}
    for grupo in ('generales', 'apartados'):
        definidos = {c['clave']: c for c in plantilla.get(grupo, [])}
        valores = contenido.get(grupo) or {}
        if not isinstance(valores, dict):
            raise ReglaRadiologia(f'{grupo}: formato no válido')
        for clave, valor in valores.items():
            campo = definidos.get(clave)
            if campo is None:
                raise ReglaRadiologia(f'{grupo}: el apartado "{clave}" no pertenece a la plantilla de este estudio')
            if valor in (None, ''):
                continue
            tipo = campo.get('tipo', 'texto')
            if tipo == 'medicion':
                if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                    raise ReglaRadiologia(f'{campo["titulo"]}: se esperaba un número')
                minimo, maximo = campo.get('minimo'), campo.get('maximo')
                if (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo):
                    raise ReglaRadiologia(f'{campo["titulo"]}: fuera del rango admitido ({minimo}–{maximo})')
                salida[grupo][clave] = valor
            elif tipo == 'opcion':
                if valor not in campo.get('opciones', []):
                    raise ReglaRadiologia(f'{campo["titulo"]}: opción no admitida')
                salida[grupo][clave] = valor
            else:
                texto = _texto(valor, MAX_TEXTO_APARTADO, campo['titulo'])
                if texto:
                    salida[grupo][clave] = texto
    return salida


def contenido_vacio(contenido: dict | None) -> bool:
    return not contenido or not (contenido.get('generales') or contenido.get('apartados'))


def _valor_legible(campo: dict, valor) -> str:
    if campo.get('tipo') == 'medicion':
        numero = f'{valor:g}'.replace('.', ',')
        return f'{numero} {campo["unidad"]}'.strip() if campo.get('unidad') else numero
    return str(valor)


def componer_informe(config: dict, contenido: dict) -> str:
    """Texto clinico del informe a partir de lo registrado, en el orden recomendado por el ACR.

    Solo incluye lo que el profesional completo.
    """
    plantilla = _plantilla(config)
    generales = contenido.get('generales') or {}
    apartados = contenido.get('apartados') or {}
    bloques: list[str] = []

    def general(clave: str) -> None:
        if generales.get(clave):
            bloques.append(f'{TITULOS_GENERALES[clave]}:\n{generales[clave]}')

    general('indicacion')
    general('tecnica')
    general('comparacion')
    hallazgos = [f'{campo["titulo"]}: {_valor_legible(campo, apartados[campo["clave"]])}'
                 for campo in plantilla.get('apartados', []) if campo['clave'] in apartados]
    if hallazgos:
        bloques.append('HALLAZGOS:\n' + '\n'.join(hallazgos))
    general('limitaciones')
    general('conclusion')
    general('recomendaciones')
    return '\n\n'.join(bloques)


def pendientes_para_validar(contenido: dict | None, texto_final: str | None, imagenes: int, externo: bool = False) -> list[str]:
    """Requisitos para validar; la conclusion la redacta siempre el medico."""
    faltan = []
    if not ((contenido or {}).get('generales') or {}).get('conclusion'):
        faltan.append('Redacta la conclusión o impresión diagnóstica.')
    if not ((contenido or {}).get('apartados') or (texto_final or '').strip()):
        faltan.append('Registra al menos un hallazgo.')
    if imagenes < 1 and not externo:
        faltan.append('El estudio no tiene imágenes asociadas.')
    return faltan


def normalizar_texto_final(texto) -> str | None:
    return _texto(texto, MAX_TEXTO_FINAL, 'texto final del informe')
