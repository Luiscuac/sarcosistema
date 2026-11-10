"""Propuestas clínicas revisables a partir de un dictado.

El modelo local clasifica y redacta cada dato en estilo clínico, citando la frase
del dictado que lo respalda. Este módulo no reinterpreta el texto: comprueba lo
verificable (que la cita exista, que las cifras y términos sensibles se hayan
dictado, que no se pierdan negaciones ni dudas) y marca lo que el médico debe
revisar. Nada de esto es una decisión clínica ni se guarda automáticamente.
"""
import math
import re
import unicodedata
from difflib import SequenceMatcher
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

NOMBRES_CAMPOS = {
    'motivo_consulta': 'Motivo de consulta', 'sintomas': 'Síntomas', 'enfermedad_actual': 'Enfermedad actual',
    'antecedentes': 'Antecedentes', 'examen_fisico': 'Examen físico', 'hallazgos': 'Hallazgos',
    'observaciones': 'Observaciones', 'evaluacion_clinica': 'Evaluación clínica',
    'diagnostico_principal': 'Diagnóstico principal', 'diagnosticos_secundarios': 'Diagnósticos secundarios',
    'tratamiento': 'Tratamiento', 'medicamentos': 'Medicamentos', 'indicaciones': 'Indicaciones',
    'estudios_solicitados': 'Estudios solicitados', 'referencias': 'Referencias',
    'recomendaciones': 'Recomendaciones', 'plan_seguimiento': 'Seguimiento', 'peso_kg': 'Peso',
    'talla_cm': 'Talla', 'temperatura_c': 'Temperatura', 'frecuencia_cardiaca': 'Frecuencia cardíaca',
    'frecuencia_respiratoria': 'Frecuencia respiratoria', 'presion_sistolica': 'Presión sistólica',
    'presion_diastolica': 'Presión diastólica', 'saturacion_oxigeno': 'Saturación de oxígeno',
}

# Rangos fisiológicamente posibles; fuera de ellos el número es un error de lectura.
RANGOS = {
    'peso_kg': (0.3, 400), 'talla_cm': (25, 250), 'temperatura_c': (30, 45),
    'frecuencia_cardiaca': (20, 260), 'frecuencia_respiratoria': (4, 90),
    'presion_sistolica': (50, 300), 'presion_diastolica': (20, 200), 'saturacion_oxigeno': (40, 100),
}
NUMERICOS = frozenset(RANGOS)
DIAGNOSTICOS = frozenset({'diagnostico_principal', 'diagnosticos_secundarios', 'evaluacion_clinica'})
# Campos donde perder un "no" / "niega" cambia el sentido clínico.
CAMPOS_CON_NEGACION = frozenset({'sintomas', 'antecedentes', 'examen_fisico', 'hallazgos', *DIAGNOSTICOS})
# Campos que en la ficha se escriben como lista separada por comas.
CAMPOS_LISTA = frozenset({
    'sintomas', 'antecedentes', 'examen_fisico', 'hallazgos', 'diagnosticos_secundarios',
    'medicamentos', 'indicaciones', 'estudios_solicitados', 'recomendaciones',
})
# Palabras propias de la redacción clínica que no cuentan como contenido nuevo.
PALABRAS_DE_REDACCION = frozenset({
    'niega', 'refiere', 'paciente', 'evolucion', 'presuntivo', 'presuntiva', 'control', 'dias', 'semana',
    'semanas', 'horas', 'meses', 'cada', 'durante', 'desde', 'hace', 'tratamiento', 'leve', 'aguda', 'agudo',
})
MIN_PALABRAS_NUEVAS = 3
MAX_VALOR = 2000
MAX_PALABRAS_CITA = 150
SIMILITUD_MINIMA_CITA = 0.75

NUMEROS_EN_PALABRAS = {
    'cero': 0, 'un': 1, 'uno': 1, 'una': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5, 'seis': 6,
    'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10, 'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14,
    'quince': 15, 'dieciseis': 16, 'diecisiete': 17, 'dieciocho': 18, 'diecinueve': 19, 'veinte': 20,
    'veintiun': 21, 'veintiuno': 21, 'veintidos': 22, 'veinticuatro': 24, 'veinticinco': 25, 'treinta': 30,
    'cuarenta': 40, 'cincuenta': 50, 'sesenta': 60, 'setenta': 70, 'ochenta': 80, 'noventa': 90,
    'cien': 100, 'ciento': 100, 'doscientos': 200, 'trescientos': 300, 'cuatrocientos': 400,
    'quinientos': 500, 'seiscientos': 600, 'ochocientos': 800, 'mil': 1000,
    'media': 0.5, 'medio': 0.5, 'semana': 7, 'semanas': 7, 'mes': 30, 'meses': 30, 'quincena': 15,
}
# Vías, unidades y formas farmacéuticas: si aparecen en el valor deben haberse dictado.
TERMINOS_SENSIBLES = {
    'vo': r'\bv\.?o\b', 'iv': r'\bi\.?v\b', 'im': r'\bi\.?m\b', 'sc': r'\bs\.?c\b', 'sl': r'\bs\.?l\b',
    'mg': r'\bmg\b', 'mcg': r'\bmcg\b', 'ml': r'\bml\b', 'g': r'\b\d+\s*g\b', 'ui': r'\bui\b',
    'via oral': r'\bvia oral\b|\boral\b', 'intravenosa': r'\bintravenos', 'intramuscular': r'\bintramuscular',
    'subcutanea': r'\bsubcutane', 'comprimido': r'\bcomprimid', 'tableta': r'\btableta', 'capsula': r'\bcapsula',
    'jarabe': r'\bjarabe', 'ampolla': r'\bampolla', 'gotas': r'\bgotas\b',
}
EQUIVALENCIAS_DICTADAS = {
    'mg': r'\bmg\b|miligramo', 'mcg': r'\bmcg\b|microgramo', 'ml': r'\bml\b|mililitro|cc\b', 'g': r'\bg\b|gramo',
    'vo': r'\bvo\b|oral|tomad|tome|boca', 'via oral': r'oral|tomad|tome|boca', 'ui': r'\bui\b|unidades',
}
NEGACION = re.compile(r'\b(?:no|niega|niegan|negad[oa]s?|sin|nunca|tampoco|ni|ninguna?|descarta)\b')
NEGACION_EN_VALOR = re.compile(r'\b(?:no|niega|negad[oa]s?|negativ[oa]s?|sin|ausencia|ninguna?|descarta|ni)\b')
DUDA = re.compile(r'\b(?:creo|parece|posible|posiblemente|probable|probablemente|sospech\w*|quizas?|presunt\w*|impresion|podria|tal vez)\b')
DUDA_EN_VALOR = re.compile(r'\b(?:presunt\w*|posible|probable|sospech\w*|a descartar|d/c|impresion)\b')
CORRECCION = re.compile(r'\b(?:perd[oó]n|corrijo|mejor dicho)\b', re.I)
APROXIMADO = re.compile(r'\b(?:creo|cerca de|aproximadamente|mas o menos|alrededor de|unos|unas)\b')
INCOMPRENSIBLE = re.compile(r'\?|\b(?:no se entiende|inaudible|no estoy seguro)\b')
OTRO_PACIENTE = re.compile(r'\b(?:otro|otra|segundo|segunda) paciente\b|\bvarios pacientes\b')

# Respaldo determinista de signos vitales dichos explícitamente.
CIFRA = r'\d{1,3}(?:[.,]\d{1,2})?'
UNIDADES_EN_PALABRAS = r'uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve'
ETIQUETAS_VITALES = {
    'temperatura_c': r'temperatura',
    'frecuencia_cardiaca': r'frecuencia\s+card[ií]aca|pulso',
    'frecuencia_respiratoria': r'frecuencia\s+respiratoria',
    'saturacion_oxigeno': r'saturaci[oó]n(?:\s+de\s+ox[ií]geno)?',
    'presion_sistolica': r'(?:presi[oó]n\s+)?sist[oó]lica',
    'presion_diastolica': r'(?:presi[oó]n\s+)?diast[oó]lica',
    'peso_kg': r'peso|pesa',
    'talla_cm': r'talla|mide|estatura',
}
TODAS_LAS_ETIQUETAS = '|'.join(ETIQUETAS_VITALES.values()) + r'|presi[oó]n'
PATRON_PRESION = re.compile(
    rf'\bpresi[oó]n(?:\s+arterial)?\b[^.;\n\d]{{0,30}}?(?P<alta>{CIFRA})\s*(?:sobre|/|con)\s*(?P<baja>{CIFRA})', re.I)
PATRON_TEMPERATURA_INVERTIDA = re.compile(rf'(?P<valor>{CIFRA})\s*(?:grados\s+)?de\s+(?:temperatura|fiebre)\b', re.I)
PATRON_TALLA_EN_METROS = re.compile(
    rf'\b(?:un|1)\s+metro\s+(?:con\s+)?(?P<cm>\d{{1,2}}\b|[a-z]+(?:\s+y\s+(?:{UNIDADES_EN_PALABRAS}))?)', re.I)
# Una cifra referida a otro momento o a un cambio no es la medición actual.
CONTEXTO_NO_ACTUAL = re.compile(
    r'\b(?:baj[oó]|bajad[oa]|subi[oó]|subid[oa]|perdi[oó]|perdid[oa]|gan[oó]|ganad[oa]|aument[oó]|aumentad[oa]'
    r'|ayer|antes|anterior|habitual)\b', re.I)


class Sugerencia(BaseModel):
    """Un dato propuesto para un campo, con la cita del dictado que lo respalda."""
    model_config = ConfigDict(extra='forbid')
    campo: CampoClinico
    valor: StrictStr | StrictFloat | StrictInt
    evidencia: str = Field(min_length=1, max_length=3000)
    ambiguo: bool = False
    alertas: list[str] = Field(default_factory=list)


class SalidaModelo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campos: list[Sugerencia] = Field(default_factory=list, max_length=25)
    multiples_pacientes: bool = False
    identidad_incierta: bool = False


class PropuestaClinica(BaseModel):
    campos: list[Sugerencia] = Field(default_factory=list)
    advertencias: list[str] = Field(default_factory=list)
    bloqueada: bool = False


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes, espacios simples y sin puntuación en los bordes."""
    sin_tildes = unicodedata.normalize('NFD', str(texto).lower())
    sin_tildes = ''.join(letra for letra in sin_tildes if unicodedata.category(letra) != 'Mn')
    return ' '.join(sin_tildes.split()).strip(' .,;:¡!¿?"\'«»')


def _palabras(texto: str) -> list[tuple[str, int, int]]:
    return [(normalizar(m.group()), m.start(), m.end()) for m in re.finditer(r'\w+', texto)]


def ubicar_cita(evidencia: str, transcripcion: str) -> str | None:
    """Devuelve el fragmento real del dictado que corresponde a la cita del modelo.

    Los modelos pequeños a veces copian la cita con pequeñas variaciones o unen frases
    que no estaban seguidas. Se busca el fragmento más parecido (o cada frase por
    separado) y se muestra al médico el texto real, nunca el reescrito por el modelo.
    """
    completa = _ubicar_fragmento(evidencia, transcripcion)
    if completa is not None:
        return completa
    frases = [frase for frase in re.split(r'(?<!\d)[.;](?!\d)', evidencia) if len(_palabras(frase)) >= 2]
    if len(frases) < 2:
        return None
    ubicadas = [_ubicar_fragmento(frase, transcripcion) for frase in frases]
    return ' … '.join(ubicadas) if None not in ubicadas else None


def _ubicar_fragmento(evidencia: str, transcripcion: str) -> str | None:
    """Fragmento continuo del dictado que coincide al menos en un 75 % con la cita."""
    cita = [palabra for palabra, _, _ in _palabras(evidencia)]
    dictado = _palabras(transcripcion)
    if not cita or len(cita) > MAX_PALABRAS_CITA or not dictado:
        return None
    mejor, rango = 0.0, None
    for largo in range(max(1, len(cita) - 3), len(cita) + 4):
        for inicio in range(len(dictado) - largo + 1):
            ventana = [palabra for palabra, _, _ in dictado[inicio:inicio + largo]]
            similitud = 1.0 if ventana == cita else SequenceMatcher(None, cita, ventana, autojunk=False).ratio()
            if similitud > mejor:
                mejor, rango = similitud, (inicio, inicio + largo)
        if mejor == 1.0:
            break
    if mejor < SIMILITUD_MINIMA_CITA:
        return None
    inicio, fin = dictado[rango[0]][1], dictado[rango[1] - 1][2]
    # Conserva los signos de pregunta/exclamación: indican que no es una afirmación.
    while inicio > 0 and transcripcion[inicio - 1] in '¿¡':
        inicio -= 1
    while fin < len(transcripcion) and transcripcion[fin] in '?!':
        fin += 1
    return transcripcion[inicio:fin]


def _palabras_a_numero(texto: str) -> float | None:
    """'setenta y cinco' -> 75, '96' -> 96, '37,5' -> 37.5."""
    texto = normalizar(texto)
    if re.fullmatch(r'\d+(?:[.,]\d+)?', texto):
        return float(texto.replace(',', '.'))
    partes = [NUMEROS_EN_PALABRAS.get(parte) for parte in texto.split() if parte != 'y']
    return float(sum(partes)) if partes and None not in partes else None


def _frase_de(transcripcion: str, inicio: int) -> str:
    """Texto desde el inicio de la frase hasta la posición dada (para leer su contexto)."""
    corte = max(transcripcion.rfind(signo, 0, inicio) for signo in '.;\n')
    return transcripcion[corte + 1:inicio]


def signos_vitales_dictados(transcripcion: str) -> list[Sugerencia]:
    """Signos vitales dichos explícitamente, como respaldo si el modelo los omite.

    Solo usa cifras literales del dictado. Si un signo se dicta con valores distintos
    sin corrección explícita, o se refiere a otro momento ("bajó de peso 3 kilos"),
    se marca ambiguo en lugar de proponerlo como medición actual.
    """
    hallados: dict[str, list[tuple[float, str, bool]]] = {}

    def agregar(campo, valor, coincidencia, evidencia=None):
        if valor is None:
            return
        evidencia = (evidencia or coincidencia.group()).strip(' ,;')
        contexto = _frase_de(transcripcion, coincidencia.start()) + evidencia
        hallados.setdefault(campo, []).append((valor, evidencia, bool(CONTEXTO_NO_ACTUAL.search(contexto))))

    def talla_en_palabras(texto_cm):
        centimetros = _palabras_a_numero(texto_cm)
        if centimetros is None:  # "un metro setenta y pesa…": se ignora lo que sigue
            centimetros = _palabras_a_numero(texto_cm.split()[0])
        return 100 + centimetros if centimetros is not None else None

    for coincidencia in PATRON_PRESION.finditer(transcripcion):
        agregar('presion_sistolica', _palabras_a_numero(coincidencia['alta']), coincidencia)
        agregar('presion_diastolica', _palabras_a_numero(coincidencia['baja']), coincidencia)
    for coincidencia in PATRON_TEMPERATURA_INVERTIDA.finditer(transcripcion):
        agregar('temperatura_c', _palabras_a_numero(coincidencia['valor']), coincidencia)
    for coincidencia in PATRON_TALLA_EN_METROS.finditer(transcripcion):
        agregar('talla_cm', talla_en_palabras(coincidencia['cm']), coincidencia)
    for campo, etiqueta in ETIQUETAS_VITALES.items():
        if campo in hallados:
            continue
        # La frase termina en punto, salvo puntos suspensivos ("39... perdón, 37") y decimales ("37.2").
        frase = r'(?:\.{2,}|[^.;\n]|(?<=\d)\.(?=\d))*'
        for coincidencia in re.finditer(rf'\b(?:{etiqueta})\b(?P<resto>{frase})', transcripcion, re.I):
            resto = re.split(rf'\b(?:{TODAS_LAS_ETIQUETAS})\b', coincidencia['resto'], maxsplit=1, flags=re.I)[0]
            cifras = re.findall(CIFRA, resto)
            if not cifras:
                continue
            corregido = CORRECCION.search(resto)
            valor = float((cifras[-1] if corregido else cifras[0]).replace(',', '.'))
            if campo == 'talla_cm' and valor < 3:
                valor = round(valor * 100)
            evidencia = transcripcion[coincidencia.start():coincidencia.start('resto') + len(resto)]
            agregar(campo, valor, coincidencia, evidencia)

    propuestas = []
    for campo, lecturas in hallados.items():
        valor, evidencia, _ = lecturas[0]
        dudoso = len({lectura[0] for lectura in lecturas}) > 1 or any(lectura[2] for lectura in lecturas)
        propuestas.append(Sugerencia(campo=campo, valor=valor, evidencia=evidencia, ambiguo=dudoso))
    return propuestas


def numeros_en(texto: str) -> set[float]:
    """Cifras escritas o en palabras simples ("tres", "quinientos") presentes en el texto."""
    normal = normalizar(texto)
    cifras = set()
    for numero in re.findall(r'\d+(?:[.,]\d+)?', normal):
        cifras.add(float(numero.replace(',', '.')))
        if ',' in numero or '.' in numero:
            cifras.update(float(parte) for parte in re.split(r'[.,]', numero))
    cifras.update(float(valor) for palabra, valor in NUMEROS_EN_PALABRAS.items()
                  if re.search(rf'\b{palabra}\b', normal))
    return cifras


def _numero_respaldado(campo: str, valor: float, evidencia: str) -> bool:
    cifras = numeros_en(evidencia)
    if valor in cifras:
        return True
    if campo == 'talla_cm':
        # "1.75 m" -> 175; "un metro setenta" -> 170.
        return round(valor / 100, 2) in cifras or ('metro' in normalizar(evidencia) and valor - 100 in cifras)
    if campo == 'temperatura_c' and valor % 1 == 0.5:
        return math.floor(valor) in cifras and re.search(r'\by medio\b', normalizar(evidencia)) is not None
    return False


def _alertas_texto(campo: str, valor: str, evidencia: str) -> list[str]:
    """Lo que el modelo agregó o perdió respecto de lo dictado y conviene verificar."""
    valor_normal, evidencia_normal = normalizar(valor), normalizar(evidencia)
    alertas = []
    cifras_nuevas = sorted(numeros_en(valor) - numeros_en(evidencia))
    if cifras_nuevas:
        alertas.append('Incluye cifras que no se dictaron: ' + ', '.join(f'{n:g}' for n in cifras_nuevas) + '.')
    terminos_nuevos = [
        termino for termino, patron in TERMINOS_SENSIBLES.items()
        if re.search(patron, valor_normal)
        and not re.search(EQUIVALENCIAS_DICTADAS.get(termino, patron), evidencia_normal)
    ]
    if terminos_nuevos:
        alertas.append('Agrega vía, unidad o forma no dictada: ' + ', '.join(terminos_nuevos) + '.')
    if campo in CAMPOS_CON_NEGACION and NEGACION.search(evidencia_normal) and not NEGACION_EN_VALOR.search(valor_normal):
        alertas.append('La frase dictada tiene una negación; confirma que el valor la conserva.')
    if NEGACION_EN_VALOR.search(valor_normal) and not NEGACION.search(evidencia_normal):
        alertas.append('Agrega una negación que no se dictó; verifícala.')
    if campo in DIAGNOSTICOS and DUDA.search(evidencia_normal) and not DUDA_EN_VALOR.search(valor_normal):
        alertas.append('El médico expresó duda; indica si es presuntivo.')
    erratas = _posibles_erratas(valor, evidencia)
    if erratas:
        alertas.append('Posible error de escritura: ' + ', '.join(erratas) + '.')
    nuevas = _palabras_no_dictadas(valor, evidencia)
    if len(nuevas) >= MIN_PALABRAS_NUEVAS and len(nuevas) * 2 > len(_palabras_de_contenido(valor)):
        alertas.append('Contiene palabras que no se dictaron (' + ', '.join(nuevas) + '); verifica que no se haya inventado.')
    return alertas


def _palabras_de_contenido(texto: str) -> list[str]:
    return [palabra for palabra, _, _ in _palabras(texto) if len(palabra) >= 4 and not palabra.isdigit()]


def _palabras_no_dictadas(valor: str, evidencia: str) -> list[str]:
    dictadas = set(_palabras_de_contenido(evidencia))
    return [palabra for palabra in dict.fromkeys(_palabras_de_contenido(valor))
            if palabra not in dictadas and palabra not in PALABRAS_DE_REDACCION]


def _posibles_erratas(valor: str, evidencia: str) -> list[str]:
    """Palabras del valor que parecen una dictada mal escrita ("Sero" por "suero")."""
    dictadas = {palabra for palabra, _, _ in _palabras(evidencia) if len(palabra) >= 4}
    erratas = []
    for palabra in dict.fromkeys(_palabras_de_contenido(valor)):
        if palabra in dictadas or palabra in PALABRAS_DE_REDACCION:
            continue
        parecida = next((dictada for dictada in dictadas if _a_una_letra(palabra, dictada)), None)
        if parecida:
            erratas.append(f'«{palabra}» (dictado: «{parecida}»)')
    return erratas


def _a_una_letra(a: str, b: str) -> bool:
    """True si difieren en exactamente una letra (cambiada, sobrante o faltante), sin contar plurales."""
    if a == b or abs(len(a) - len(b)) > 1 or a.rstrip('s') == b.rstrip('s'):
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    corta, larga = sorted((a, b), key=len)
    return any(larga[:i] + larga[i + 1:] == corta for i in range(len(larga)))


def formato_lista(valor: str) -> str:
    """'Dolor de garganta. Fiebre. Tos seca.' -> 'Dolor de garganta, fiebre, tos seca'.

    Solo cambia separadores entre elementos; no toca decimales ("38.5") ni siglas.
    """
    partes = [parte.strip() for parte in re.split(r'(?<!\d)[.;]\s+|(?<!\d)[.;]$', valor.strip()) if parte.strip()]

    def en_minuscula(parte: str) -> str:
        primera = parte.split()[0]
        return parte if primera.isupper() and len(primera) > 1 else parte[0].lower() + parte[1:]

    return ', '.join([partes[0], *map(en_minuscula, partes[1:])]) if partes else valor


def _quitar_presuntivo_injustificado(campo: str, valor: str, evidencia: str) -> str:
    """Quita "(presuntivo)" si el médico no expresó duda o el texto ya dice "sospecha"/"posible"."""
    if campo not in DIAGNOSTICOS:
        return valor
    sin_marca = re.sub(r'\s*\(presuntiv[oa]\)', '', valor, flags=re.I)
    if not DUDA.search(normalizar(evidencia)) or DUDA_EN_VALOR.search(normalizar(sin_marca)):
        return sin_marca
    return valor


def _revisar_numerico(item: Sugerencia) -> tuple[Sugerencia | None, str | None]:
    valor = item.valor
    if isinstance(valor, str):
        try:
            valor = float(valor.replace(',', '.'))
        except ValueError:
            return None, f'{NOMBRES_CAMPOS[item.campo]}: el valor no es un número; introdúcelo manualmente.'
    minimo, maximo = RANGOS[item.campo]
    if not math.isfinite(valor) or not minimo <= valor <= maximo:
        return None, f'{NOMBRES_CAMPOS[item.campo]}: valor fuera de un rango posible; introdúcelo manualmente.'
    valor = int(valor) if float(valor).is_integer() else float(valor)
    ambiguo, alertas = item.ambiguo, list(item.alertas)
    if not _numero_respaldado(item.campo, valor, item.evidencia):
        ambiguo = True
        alertas.append('El número no aparece tal cual en lo dictado; escríbelo manualmente.')
    if APROXIMADO.search(normalizar(item.evidencia)):
        ambiguo = True
        alertas.append('La medición se dictó como aproximada.')
    if item.campo == 'temperatura_c' and re.search(r'fahrenheit|\b°?f\b', normalizar(item.evidencia)):
        ambiguo = True
        alertas.append('La temperatura se dictó en Fahrenheit.')
    return item.model_copy(update={'valor': valor, 'ambiguo': ambiguo, 'alertas': alertas}), None


def _revisar_texto(item: Sugerencia) -> tuple[Sugerencia | None, str | None]:
    valor = ' '.join(str(item.valor).split())
    if not valor:
        return None, f'{NOMBRES_CAMPOS[item.campo]}: la propuesta estaba vacía.'
    if len(valor) > MAX_VALOR:
        return None, f'{NOMBRES_CAMPOS[item.campo]}: la propuesta es demasiado larga; revísala manualmente.'
    valor = _quitar_presuntivo_injustificado(item.campo, valor, item.evidencia)
    valor = formato_lista(valor) if item.campo in CAMPOS_LISTA else valor
    alertas = list(item.alertas) + _alertas_texto(item.campo, valor, item.evidencia)
    return item.model_copy(update={'valor': valor, 'alertas': alertas}), None


def _presiones_coherentes(campos: list[Sugerencia]) -> list[Sugerencia]:
    por_campo = {item.campo: item for item in campos}
    sistolica, diastolica = por_campo.get('presion_sistolica'), por_campo.get('presion_diastolica')
    if not sistolica or not diastolica or sistolica.valor > diastolica.valor:
        return campos
    aviso = 'La sistólica debe ser mayor que la diastólica.'
    return [item.model_copy(update={'ambiguo': True, 'alertas': [*item.alertas, aviso]})
            if item.campo in ('presion_sistolica', 'presion_diastolica') else item for item in campos]


def _revisar(item: Sugerencia) -> tuple[Sugerencia | None, str | None]:
    """Aplica las comprobaciones del tipo de campo a una propuesta con cita ya ubicada."""
    revisado, aviso = (_revisar_numerico if item.campo in NUMERICOS else _revisar_texto)(item)
    # Sobre la cita original: normalizar() quitaría los signos de pregunta.
    if revisado is not None and INCOMPRENSIBLE.search(revisado.evidencia.lower()):
        revisado = revisado.model_copy(update={'ambiguo': True})
    return revisado, aviso


def _aviso_sin_respaldo(campos: list[str]) -> str:
    if len(campos) > 4:
        return f'Se descartaron {len(campos)} propuestas que no estaban respaldadas por lo dictado.'
    return 'Se descartaron propuestas no respaldadas por lo dictado: ' + ', '.join(campos) + '.'


def _contrastar_con_dictado(item: Sugerencia, dictados: dict[str, Sugerencia]) -> Sugerencia:
    """Un signo vital del modelo que no coincide con lo leído literalmente del dictado.

    Si el médico se corrigió ("39, perdón, 37"), vale la lectura literal corregida.
    Si solo difieren, el dato queda ambiguo para que el médico lo confirme.
    """
    leido = dictados.get(item.campo)
    if item.campo not in NUMERICOS or leido is None:
        return item
    try:
        valor = float(str(item.valor).replace(',', '.'))
    except ValueError:
        return item
    if valor == leido.valor:
        return item
    if CORRECCION.search(leido.evidencia):
        return leido
    aviso = f'Lo dictado parece indicar {leido.valor:g}; confírmalo.'
    return item.model_copy(update={'ambiguo': True, 'alertas': [*item.alertas, aviso]})


def validar_propuesta(salida: SalidaModelo, transcripcion: str) -> PropuestaClinica:
    """Verifica cada propuesta contra el dictado; descarta lo no respaldado y marca lo dudoso."""
    if OTRO_PACIENTE.search(normalizar(transcripcion)):
        return PropuestaClinica(bloqueada=True, advertencias=[
            'El dictado menciona a más de un paciente. Revisa la transcripción; no se aplicaron datos.'
        ])
    resultado = PropuestaClinica()
    if salida.multiples_pacientes or salida.identidad_incierta:
        resultado.advertencias.append('El modelo indicó que el dictado podría no ser de un solo paciente; verifícalo.')

    dictados = {item.campo: item for item in signos_vitales_dictados(transcripcion)}
    del_modelo = [_contrastar_con_dictado(item, dictados) for item in salida.campos]
    propuestos = {item.campo for item in salida.campos}
    respaldo = [item for campo, item in dictados.items() if campo not in propuestos]
    contenidos: dict[str, str] = {}
    sin_respaldo: list[str] = []
    for item in [*del_modelo, *respaldo]:
        if item.campo in contenidos:
            continue  # Se conserva la primera propuesta de cada campo.
        cita = ubicar_cita(item.evidencia, transcripcion)
        if cita is None:
            sin_respaldo.append(NOMBRES_CAMPOS[item.campo])
            continue
        revisado, aviso = _revisar(item.model_copy(update={'evidencia': cita}))
        if aviso:
            resultado.advertencias.append(aviso)
        if revisado is None:
            continue
        if revisado.campo not in NUMERICOS:
            repetido = next((campo for campo, valor in contenidos.items() if valor == normalizar(revisado.valor)), None)
            if repetido:
                aviso_repetido = f'Repite el contenido de {NOMBRES_CAMPOS[repetido]}.'
                revisado = revisado.model_copy(update={'alertas': [*revisado.alertas, aviso_repetido]})
        contenidos[revisado.campo] = normalizar(revisado.valor)
        resultado.campos.append(revisado)

    resultado.campos = _presiones_coherentes(resultado.campos)
    if sin_respaldo:
        resultado.advertencias.append(_aviso_sin_respaldo(list(dict.fromkeys(sin_respaldo))))
    if any(item.ambiguo for item in resultado.campos):
        resultado.advertencias.append('Hay datos ambiguos: complétalos manualmente.')
    resultado.advertencias = list(dict.fromkeys(resultado.advertencias))
    return resultado
