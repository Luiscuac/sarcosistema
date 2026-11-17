"""Plantillas de registro manual; no completan hallazgos ni conclusiones."""
from datetime import date

from app.imagenes.domain.errors import SolicitudInvalida

ORGANOS = {
    'ECO_ABDOMINAL': ('Hígado', 'Vías biliares', 'Vesícula biliar', 'Páncreas', 'Bazo', 'Riñón derecho', 'Riñón izquierdo'),
    'ECO_OBSTETRICA': ('Embrión o feto', 'Líquido amniótico', 'Placenta', 'Cordón umbilical'),
    'ECO_GINECOLOGICA': ('Útero', 'Ovarios', 'Trompas de Falopio', 'Fondo de saco de Douglas'),
    'ECO_RENAL': ('Riñón derecho', 'Riñón izquierdo', 'Vías urinarias', 'Vejiga'),
    'ECO_PARTES_BLANDAS': ('Piel', 'Tejido subcutáneo', 'Músculos', 'Tendones', 'Ganglios de la zona estudiada'),
    'ECO_TIROIDEA': ('Lóbulo tiroideo derecho', 'Lóbulo tiroideo izquierdo', 'Istmo tiroideo', 'Ganglios cervicales'),
    'ECO_MAMARIA': ('Glándula mamaria derecha', 'Glándula mamaria izquierda', 'Región axilar derecha', 'Región axilar izquierda'),
    'ECO_DOPPLER': ('Arterias de la zona estudiada', 'Venas de la zona estudiada'),
}


def validar_datos(datos: dict, codigo: str, publicar: bool = False) -> dict:
    campos = {'version', 'tipo', 'fecha_estudio', 'establecimiento', 'zona', 'evaluaciones', 'conclusion', 'observaciones'}
    if not isinstance(datos, dict) or set(datos) - campos or codigo not in ORGANOS:
        raise SolicitudInvalida('La plantilla de ecografía no es válida para este estudio.')
    if type(datos.get('version')) is not int or datos.get('version') != 1 or datos.get('tipo') != codigo:
        raise SolicitudInvalida('La plantilla no corresponde al tipo de ecografía.')
    resultado = {'version': 1, 'tipo': codigo}
    for campo, limite in [('fecha_estudio', 10), ('establecimiento', 200), ('zona', 300), ('conclusion', 4000), ('observaciones', 4000)]:
        valor = datos.get(campo, '')
        if not isinstance(valor, str) or len(valor) > limite:
            raise SolicitudInvalida('Los datos del informe exceden el formato permitido.')
        resultado[campo] = valor.strip()
    try:
        if resultado['fecha_estudio']:
            if date.fromisoformat(resultado['fecha_estudio']).isoformat() != resultado['fecha_estudio']:
                raise ValueError
    except ValueError:
        raise SolicitudInvalida('La fecha del estudio no es válida.') from None
    evaluaciones = datos.get('evaluaciones', {})
    if not isinstance(evaluaciones, dict) or set(evaluaciones) - set(ORGANOS[codigo]):
        raise SolicitudInvalida('El informe contiene órganos ajenos a su plantilla.')
    resultado['evaluaciones'] = {}
    for organo in ORGANOS[codigo]:
        valor = evaluaciones.get(organo, '')
        if not isinstance(valor, str) or len(valor) > 2000:
            raise SolicitudInvalida('Cada observación debe tener como máximo 2000 caracteres.')
        resultado['evaluaciones'][organo] = valor.strip()
    if publicar:
        if not resultado['fecha_estudio'] or not resultado['conclusion'] or not all(resultado['evaluaciones'].values()):
            raise InformeIncompleto('Completa la fecha, la conclusión y cada órgano. Si no se evaluó, indícalo expresamente.')
        if codigo in ('ECO_PARTES_BLANDAS', 'ECO_DOPPLER') and not resultado['zona']:
            raise InformeIncompleto('Indica la zona u órgano estudiado.')
    return resultado


class InformeIncompleto(SolicitudInvalida):
    pass


def texto_informe(datos: dict) -> str:
    partes = [f'{organo.upper()}: {valor}' for organo, valor in datos['evaluaciones'].items() if valor]
    if datos.get('zona'):
        partes.insert(0, 'ZONA ESTUDIADA: ' + datos['zona'])
    if datos.get('observaciones'):
        partes.append('OBSERVACIONES: ' + datos['observaciones'])
    if datos.get('conclusion'):
        partes.append('CONCLUSIÓN: ' + datos['conclusion'])
    return '\n\n'.join(partes)
