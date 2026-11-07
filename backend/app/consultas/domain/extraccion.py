"""Contrato extractivo: propuestas, no decisiones clínicas ni contenido definitivo."""
import math
import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr

CampoClinico = Literal[
    'motivo_consulta', 'sintomas', 'enfermedad_actual', 'antecedentes',
    'examen_fisico', 'hallazgos', 'observaciones', 'evaluacion_clinica',
    'diagnostico_principal', 'diagnosticos_secundarios', 'tratamiento',
    'medicamentos', 'indicaciones', 'estudios_solicitados', 'referencias',
    'recomendaciones', 'plan_seguimiento', 'peso_kg', 'talla_cm',
    'temperatura_c', 'frecuencia_cardiaca', 'frecuencia_respiratoria',
    'presion_sistolica', 'presion_diastolica', 'saturacion_oxigeno',
]
NUMERICOS = frozenset({'peso_kg', 'talla_cm', 'temperatura_c', 'frecuencia_cardiaca',
    'frecuencia_respiratoria', 'presion_sistolica', 'presion_diastolica', 'saturacion_oxigeno'})
FIN_FRASE = re.compile(r'(?<!\.)[.!?\n](?!\.)(?!(?<=\d\.)\d)')
ETIQUETAS_DICTADO = re.compile(
    r'(?P<etiqueta>motivo(?:\s+de\s+consulta)?|s[ií]ntomas?|enfermedad\s+actual|'
    r'antecedentes?(?:\s+relevantes)?|al\s+examen\s+f[ií]sico|examen\s+f[ií]sico|'
    r'hallazgos(?:\s+cl[ií]nicos)?|observaciones|'
    r'evaluaci[oó]n\s+cl[ií]nica|diagn[oó]stico\s+principal|diagn[oó]sticos?\s+secundarios?|'
    r'tratamiento|medicamentos(?:\s+indicados)?|indicaciones(?:\s+m[eé]dicas)?|'
    r'estudios(?:\s+complementarios)?\s+solicitados|'
    r'referencias(?:\s+y\s+contrarreferencias)?|recomendaciones|'
    r'plan(?:\s+de\s+acci[oó]n)?|seguimiento|frecuencia\s+card[ií]aca|pulso|'
    r'frecuencia\s+respiratoria|presi[oó]n\s+sist[oó]lica|sist[oó]lica|'
    r'presi[oó]n\s+diast[oó]lica|diast[oó]lica|saturaci[oó]n(?:\s+de\s+ox[ií]geno)?|'
    r'temperatura|peso|talla)\b\s*(?::|,)?',
    re.IGNORECASE,
)

ROTULOS_CAMPOS = {
    'motivo de consulta': 'motivo_consulta', 'motivo': 'motivo_consulta',
    'sintomas': 'sintomas', 'sintoma': 'sintomas',
    'enfermedad actual': 'enfermedad_actual', 'antecedentes': 'antecedentes',
    'antecedente': 'antecedentes', 'antecedentes relevantes': 'antecedentes',
    'antecedente relevante': 'antecedentes', 'al examen fisico': 'examen_fisico',
    'examen fisico': 'examen_fisico', 'hallazgos': 'hallazgos',
    'hallazgos clinicos': 'hallazgos',
    'observaciones': 'observaciones', 'evaluacion clinica': 'evaluacion_clinica',
    'diagnostico principal': 'diagnostico_principal',
    'diagnostico secundario': 'diagnosticos_secundarios',
    'diagnosticos secundarios': 'diagnosticos_secundarios',
    'tratamiento': 'tratamiento', 'medicamentos': 'medicamentos',
    'medicamentos indicados': 'medicamentos',
    'indicaciones': 'indicaciones', 'indicaciones medicas': 'indicaciones',
    'estudios solicitados': 'estudios_solicitados',
    'estudios complementarios solicitados': 'estudios_solicitados',
    'referencias': 'referencias', 'referencias y contrarreferencias': 'referencias',
    'recomendaciones': 'recomendaciones',
    'plan': 'plan_seguimiento', 'plan de accion': 'plan_seguimiento',
    'seguimiento': 'plan_seguimiento',
}


def campo_de_rotulo(segmento: str) -> str | None:
    coincidencia = ETIQUETAS_DICTADO.match(segmento)
    if not coincidencia:
        return None
    rotulo = unicodedata.normalize('NFD', coincidencia.group('etiqueta').lower())
    rotulo = ''.join(letra for letra in rotulo if unicodedata.category(letra) != 'Mn')
    return ROTULOS_CAMPOS.get(' '.join(rotulo.split()))


def valor_textual(campo: str, evidencia: str) -> str:
    """Quita solo un rótulo explícito y, en síntomas, separa lo negado."""
    valor = evidencia
    if campo_de_rotulo(evidencia) == campo:
        valor = evidencia[ETIQUETAS_DICTADO.match(evidencia).end():].lstrip(' \t,;:.')
    if campo == 'sintomas':
        valor = re.split(r'\s*[,;.]?\s*\b(?:niega|no presenta)\b', valor, maxsplit=1, flags=re.I)[0]
    return valor.strip(' \t,;')


def segmentos_dictado_rotulado(texto: str) -> list[str]:
    """Divide transcripciones con comas solo en rótulos clínicos explícitos."""
    rotulos = []
    for coincidencia in ETIQUETAS_DICTADO.finditer(texto):
        prefijo = texto[:coincidencia.start('etiqueta')].rstrip()
        if prefijo and prefijo[-1] not in ',;.!?\n':
            continue
        rotulos.append(coincidencia.start('etiqueta'))

    segmentos = []
    for indice, inicio in enumerate(rotulos):
        fin = rotulos[indice + 1] if indice + 1 < len(rotulos) else len(texto)
        segmento = texto[inicio:fin].strip(' \t,;')
        if segmento:
            segmentos.append(segmento)
    return segmentos


ETIQUETAS_MEDICIONES = {
    'peso_kg': r'\b(?:peso|pesa)\b', 'talla_cm': r'\b(?:talla|mide)\b',
    'temperatura_c': r'\btemperatura\b',
    'frecuencia_cardiaca': r'\b(?:frecuencia card[ií]aca|pulso)\b',
    'frecuencia_respiratoria': r'\bfrecuencia respiratoria\b',
    'presion_sistolica': r'\b(?:presi[oó]n|sist[oó]lica)\b',
    'presion_diastolica': r'\b(?:presi[oó]n|diast[oó]lica)\b',
    'saturacion_oxigeno': r'\bsaturaci[oó]n\b',
}


def contexto_medicion(campo: str, evidencia: str) -> str:
    """No atribuir una negación/fecha de otro dato a la medición explícita."""
    partes = re.split(r'(?<!\d),(?!\d)|;|\s+y\s+', evidencia, flags=re.I)
    propias = [parte for parte in partes if re.search(ETIQUETAS_MEDICIONES[campo], parte, re.I)]
    return propias[0] if len(propias) == 1 else evidencia



class Sugerencia(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campo: CampoClinico
    valor: StrictStr | StrictFloat | StrictInt
    evidencia: str = Field(min_length=1, max_length=3000)
    ambiguo: bool = False


class SalidaModelo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campos: list[Sugerencia] = Field(default_factory=list, max_length=24)
    campos_sin_sentido: list[CampoClinico] = Field(default_factory=list, max_length=24)
    multiples_pacientes: bool = False
    identidad_incierta: bool = False


class PropuestaClinica(BaseModel):
    campos: list[Sugerencia] = Field(default_factory=list)
    advertencias: list[str] = Field(default_factory=list)
    bloqueada: bool = False


def numero_respaldado(campo: str, valor: float, evidencia: str) -> bool:
    """Conversión limitada y verificable; lo no verificable se descarta, no se adivina."""
    if not math.isfinite(valor) or valor <= 0 or (campo == 'saturacion_oxigeno' and valor > 100):
        return False
    # Normaliza solo comas decimales; conserva la coma después de un rótulo
    # ("Presión diastólica, 80") para que también pueda validarse como separador.
    texto = re.sub(r'(?<=\d),(?=\d)', '.', evidencia.lower())
    if campo == 'temperatura_c' and re.search(r'fahrenheit|[°º]\s*f\b|\d\s*f\b', contexto_medicion(campo, texto)):
        return False
    # La corrección explícita más reciente prevalece, conservando evidencia original.
    corregido = re.split(r'\b(?:perdón|perdon|corrijo|corrección|correccion)\b', texto)
    if len(corregido) > 1:
        etiquetas = {
            'peso_kg': r'\b(?:peso|pesa)\b', 'talla_cm': r'\b(?:talla|mide)\b',
            'temperatura_c': r'\btemperatura\b',
            'frecuencia_cardiaca': r'\b(?:frecuencia card[ií]aca|pulso)\b',
            'frecuencia_respiratoria': r'\bfrecuencia respiratoria\b',
            'presion_sistolica': r'\bsist[oó]lica\b',
            'presion_diastolica': r'\bdiast[oó]lica\b',
            'saturacion_oxigeno': r'\bsaturaci[oó]n\b',
        }
        # Una correccion no puede decidir entre dos mediciones de la misma frase.
        if sum(bool(re.search(patron, texto)) for patron in etiquetas.values()) != 1:
            return False
        if not re.search(etiquetas[campo], texto):
            return False
        numeros = re.findall(r'\d+(?:\.\d+)?', corregido[-1])
        return len(numeros) == 1 and float(numeros[0]) == valor
    numero = r'(\d+(?:\.\d+)?)'
    separador_rotulo = r'\s*[:,]?\s*'
    patrones = {
        'peso_kg': rf'(?:pesa|peso(?:\s+de)?)\s*{separador_rotulo}{numero}\s*(?:kilos?|kg|kilogramos?)',
        'temperatura_c': rf'(?:temperatura(?:\s+de)?)\s*{separador_rotulo}{numero}',
        'frecuencia_cardiaca': rf'(?:frecuencia card[ií]aca|pulso)\s*{separador_rotulo}{numero}',
        'frecuencia_respiratoria': rf'(?:frecuencia respiratoria)\s*{separador_rotulo}{numero}',
        'saturacion_oxigeno': rf'(?:saturaci[oó]n(?: de ox[ií]geno)?(?:\s+de)?)\s*{separador_rotulo}{numero}',
    }
    if campo in ('presion_sistolica', 'presion_diastolica'):
        pares = re.findall(rf'(?:presi[oó]n(?: arterial)?(?:\s+de)?)[^\d]{{0,10}}{numero}\s*(?:sobre|/|con)\s*{numero}', texto)
        if pares:
            indice = 0 if campo == 'presion_sistolica' else 1
            return len(pares) == 1 and float(pares[0][indice]) == valor
        etiqueta = 'sist[oó]lica' if campo == 'presion_sistolica' else 'diast[oó]lica'
        patron = rf'{etiqueta}\s*{separador_rotulo}{numero}'
    elif campo == 'talla_cm':
        palabras = {'cincuenta': 50, 'sesenta': 60, 'setenta': 70, 'ochenta': 80, 'noventa': 90}
        verbal = re.search(r'\bun metro (cincuenta|sesenta|setenta|ochenta|noventa)\b', texto)
        if verbal:
            return valor == 100 + palabras[verbal[1]]
        metros = re.search(rf'(?:mide|talla(?:\s+de)?)\s*{separador_rotulo}{numero}\s*(?:metros?|m)\b', texto)
        if metros:
            return math.isclose(float(metros[1]) * 100, valor)
        patron = rf'(?:mide|talla(?:\s+de)?)\s*{separador_rotulo}{numero}\s*(?:cm|cent[ií]metros?)'
    else:
        patron = patrones.get(campo)
    coincidencias = re.findall(patron, texto) if patron else []
    return len(coincidencias) == 1 and float(coincidencias[0]) == valor


ROTULOS_MEDICION = {
    'peso_kg': r'\b(?:peso|pesa)\b', 'talla_cm': r'\b(?:talla|mide)\b',
    'temperatura_c': r'\btemperatura\b',
    'frecuencia_cardiaca': r'\b(?:frecuencia card[ií]aca|pulso)\b',
    'frecuencia_respiratoria': r'\bfrecuencia respiratoria\b',
    'presion_sistolica': r'\b(?:presi[oó]n(?: arterial)?|sist[oó]lica)\b',
    'presion_diastolica': r'\b(?:presi[oó]n(?: arterial)?|diast[oó]lica)\b',
    'saturacion_oxigeno': r'\bsaturaci[oó]n(?: de ox[ií]geno)?\b',
}


def evidencia_medicion(campo: str, valor: float, frase: str) -> str:
    """Cita la medición, sin arrastrar la cláusula siguiente del dictado."""
    if re.search(r'\b(?:perd[oó]n|corrijo|correcci[oó]n|creo|quiz[aá]s?|'
                 r'aproximadamente|cerca de|ayer|antes|no se entiende|inaudible)\b', frase, re.I):
        return frase
    rotulo = ROTULOS_MEDICION[campo]
    for coincidencia in re.finditer(rotulo, frase, re.I):
        resto = frase[coincidencia.start():]
        numeros = list(re.finditer(r'\d+(?:[.,]\d+)?', resto))
        if not numeros:
            continue
        # El primer número debe estar junto al rótulo; en presión 120/80
        # se necesitan ambos valores para verificar sistólica y diastólica.
        if numeros[0].start() > 24:
            continue
        es_par = (campo.startswith('presion_') and len(numeros) > 1
                  and re.fullmatch(r'\s*(?:sobre|/|con)\s*', resto[numeros[0].end():numeros[1].start()], re.I))
        fin = numeros[1].end() if es_par else numeros[0].end()
        candidato = resto[:fin].strip(' \t,;')
        if numero_respaldado(campo, valor, candidato):
            return candidato
    return frase


def mediciones_explicitas(texto: str) -> list[Sugerencia]:
    """Complemento determinista del LLM, SOLO para medidas explícitas verificables."""
    inicios = [0] + [m.end() for m in FIN_FRASE.finditer(texto)]
    if inicios[-1] != len(texto):
        inicios.append(len(texto))
    frases = segmentos_dictado_rotulado(texto) + [
        texto[inicio:fin].strip()
        for inicio, fin in zip(inicios, inicios[1:])
    ]
    encontradas = {}
    for frase in dict.fromkeys(frases):
        if not frase or len(frase) > 3000:
            continue
        numeros = {float(n.replace(',', '.')) for n in re.findall(r'\d+(?:[.,]\d+)?', frase)}
        candidatos = numeros | {n * 100 for n in numeros} | {150, 160, 170, 180, 190}
        for campo in NUMERICOS:
            valores = [n for n in candidatos if numero_respaldado(campo, n, frase)]
            if len(valores) == 1:
                evidencia = evidencia_medicion(campo, valores[0], frase)
                encontradas.setdefault(campo, []).append(Sugerencia(campo=campo, valor=valores[0], evidencia=evidencia))
    salida = []
    for items in encontradas.values():
        distintos = {item.valor for item in items}
        mas_precisa = min(items, key=lambda item: len(item.evidencia))
        salida.append(mas_precisa.model_copy(update={'ambiguo': len(distintos) > 1}))
    return salida


def validar_propuesta(salida: SalidaModelo, transcripcion: str) -> PropuestaClinica:
    resultado = PropuestaClinica()
    if (salida.multiples_pacientes or salida.identidad_incierta
            or re.search(r'\b(?:otro paciente|otra paciente|segundo paciente|segunda paciente|varios pacientes)\b', transcripcion, re.I)):
        return PropuestaClinica(bloqueada=True, advertencias=[
            'No se puede atribuir con seguridad el texto a un solo paciente. Revisa la transcripción; no se aplicaron datos.'
        ])
    medidas = mediciones_explicitas(transcripcion)
    campos_medidos = {item.campo for item in medidas}
    # Resolver tipos/unidades mediante comprobación explícita, no por estimación del modelo.
    segmentos = segmentos_dictado_rotulado(transcripcion)
    campos_modelo = {item.campo for item in salida.campos}
    # Recupera campos narrativos con rótulos SOAP inequívocos aunque el modelo
    # omita una propuesta. El valor sale solo del segmento literal delimitado
    # por rótulos; no se infiere ni se completa contenido clínico.
    recuperables = tuple(dict.fromkeys(ROTULOS_CAMPOS.values()))
    campos_sin_sentido = set(salida.campos_sin_sentido)
    recuperadas = []
    for campo in recuperables:
        if campo in campos_modelo or campo in campos_sin_sentido:
            continue
        rotuladas = [segmento for segmento in segmentos if campo_de_rotulo(segmento) == campo]
        if len(rotuladas) == 1:
            evidencia = rotuladas[0]
            recuperadas.append(Sugerencia(campo=campo, valor=evidencia, evidencia=evidencia))
    candidatos = [item for item in salida.campos
                  if item.campo not in campos_medidos and item.campo not in campos_sin_sentido]
    candidatos += medidas + recuperadas
    vistos = set()
    for item in candidatos:
        if (item.campo == 'motivo_consulta'
                and re.search(r'\b(?:paciente presenta|paciente refiere)\b', item.evidencia, re.I)
                and re.search(r'\bniega\b', item.evidencia, re.I)
                and not re.search(r'\b(?:motivo|consulta por|viene por)\b', item.evidencia, re.I)):
            item = item.model_copy(update={'campo': 'sintomas'})
        evidencia_propuesta = item.evidencia
        if evidencia_propuesta not in transcripcion:
            resultado.advertencias.append(f'{item.campo}: evidencia ausente; no se aplicó.')
            continue
        if item.campo in vistos:
            indice = next(i for i, aceptada in enumerate(resultado.campos) if aceptada.campo == item.campo)
            aceptada = resultado.campos[indice]
            if evidencia_propuesta not in aceptada.evidencia:
                resultado.campos[indice] = aceptada.model_copy(update={'ambiguo': True})
                resultado.advertencias.append(f'{item.campo}: el modelo propuso citas distintas; revisa el original.')
            continue
        # Tambien las mediciones: una cita recortada ('temperatura 36.5') no debe
        # descartarse por una negacion que vive en otro segmento del dictado.
        rotulados = [segmento for segmento in segmentos
                     if campo_de_rotulo(segmento) == item.campo and evidencia_propuesta in segmento]
        if not rotulados and item.campo in NUMERICOS:
            etiqueta = ROTULOS_MEDICION.get(item.campo)
            if etiqueta:
                rotulados = [segmento for segmento in segmentos
                             if re.match(etiqueta, segmento.strip(), re.I)
                             and evidencia_propuesta in segmento]
        if len(rotulados) == 1:
            segmento = rotulados[0]
            if segmento != evidencia_propuesta:
                # El segmento del dictado puede arrastrar clausulas ajenas
                # ("... grados Celsius, niega vomitos"); se citra solo la propia.
                etiqueta = ROTULOS_MEDICION.get(item.campo)
                partes = re.split(r'(?<!\d),(?!\d)|;|\s+y\s+', segmento, flags=re.I)
                if etiqueta:
                    propias = [parte.strip() for parte in partes
                               if re.search(r'\d', parte) and re.match(etiqueta, parte.strip(), re.I)]
                    if len(propias) == 1:
                        segmento = propias[0]
            item = item.model_copy(update={'evidencia': segmento})
        # No confiar en citas recortadas que omitan negación, dosis o una corrección posterior.
        posicion = transcripcion.index(item.evidencia)
        fin = posicion + len(item.evidencia)
        limites = list(FIN_FRASE.finditer(transcripcion))
        izquierda = max((m.end() for m in limites if m.end() <= posicion), default=0)
        derecha = min((m.end() for m in limites if m.end() >= fin), default=len(transcripcion))
        contexto = transcripcion[izquierda:derecha]
        es_oracion_completa = contexto.strip(' .!?\n\r\t') == item.evidencia.strip(' .!?\n\r\t')
        es_segmento_rotulado = item.evidencia in segmentos
        es_medicion_verificable = (item.campo in NUMERICOS and not isinstance(item.valor, str)
                                  and numero_respaldado(item.campo, item.valor, item.evidencia)
                                  and not re.search(r'\b(?:perd[oó]n|corrijo|correcci[oó]n)\b',
                                                    contexto[fin - izquierda:], re.I))
        if not es_oracion_completa and not es_segmento_rotulado and not es_medicion_verificable:
            resultado.advertencias.append(f'{item.campo}: la evidencia omitía parte de la frase; revisa el texto completo.')
            continue
        ambigua = item.ambiguo or bool(re.search(
            r'\?|\b(?:pregunta|creo|quiz[aá]s?|aproximadamente|cerca de|no se entiende|inaudible|no estoy seguro)\b', item.evidencia, re.I))
        if item.campo in ('diagnostico_principal', 'diagnosticos_secundarios') and re.search(
                r'\b(?:antecedentes?|hist[oó]rico|hace a[ñn]os)\b', item.evidencia, re.I):
            ambigua = True
        if item.campo in ('diagnostico_principal', 'diagnosticos_secundarios') and re.search(
                r'\b(?:niega|descarta|descartado|descartada)\b', item.evidencia, re.I):
            ambigua = True
        contexto_ambiguedad = (contexto_medicion(item.campo, item.evidencia) if item.campo in NUMERICOS else item.evidencia)
        if item.campo in NUMERICOS and re.search(r'\b(?:ayer|antes|hist[oó]ric[oa]|niega|negad[oa])\b', contexto_ambiguedad, re.I):
            ambigua = True
        if item.campo in NUMERICOS:
            if isinstance(item.valor, str) or not numero_respaldado(item.campo, item.valor, item.evidencia):
                if (ambigua and not isinstance(item.valor, str) and math.isfinite(item.valor)
                        and item.valor > 0 and format(item.valor, 'g') in item.evidencia):
                    resultado.campos.append(item.model_copy(update={'ambiguo': True}))
                    continue
                resultado.advertencias.append(f'{item.campo}: medición o unidad no verificable; introdúcela manualmente.')
                continue
        elif not isinstance(item.valor, str) or item.valor != evidencia_propuesta:
            resultado.advertencias.append(f'{item.campo}: el texto no era literal; revisa el original.')
            continue
        else:
            valor = valor_textual(item.campo, item.evidencia)
            if not valor:
                resultado.advertencias.append(f'{item.campo}: no hay un valor afirmado para proponer; revisa el original.')
                continue
            item = item.model_copy(update={'valor': valor})
        posicion = transcripcion.index(item.evidencia)
        inicio = max(transcripcion.rfind('.', 0, posicion), transcripcion.rfind('\n', 0, posicion)) + 1
        prefijo = transcripcion[inicio:posicion]
        # En dictados rotulados puede haber campos previos con negaciones; no
        # deben contaminar un segmento posterior ya delimitado y validado.
        if not es_segmento_rotulado and re.search(
                r'\b(?:niega|sin|no|posible|sospecha|descartar)\b', prefijo, re.I):
            resultado.advertencias.append(f'{item.campo}: evidencia recortada o contexto de negación; revisa el original.')
            continue
        resultado.campos.append(item.model_copy(update={'ambiguo': ambigua}))
        vistos.add(item.campo)
    if any(item.ambiguo for item in resultado.campos):
        resultado.advertencias.append('Hay información ambigua. Revisa y resuelve esos campos manualmente.')
    resultado.advertencias = list(dict.fromkeys(resultado.advertencias))
    return resultado
