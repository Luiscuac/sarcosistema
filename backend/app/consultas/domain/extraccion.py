"""Contrato extractivo: propuestas, no decisiones clínicas ni contenido definitivo."""
import math
import re
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


class Sugerencia(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campo: CampoClinico
    valor: StrictStr | StrictFloat | StrictInt
    evidencia: str = Field(min_length=1, max_length=3000)
    ambiguo: bool = False


class SalidaModelo(BaseModel):
    model_config = ConfigDict(extra='forbid')
    campos: list[Sugerencia] = Field(default_factory=list, max_length=24)
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
    texto = evidencia.lower().replace(',', '.')
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
        if not re.search(etiquetas[campo], texto):
            return False
        numeros = re.findall(r'\d+(?:\.\d+)?', corregido[-1])
        return len(numeros) == 1 and float(numeros[0]) == valor
    numero = r'(\d+(?:\.\d+)?)'
    patrones = {
        'peso_kg': rf'(?:pesa|peso(?:\s+de)?)\s*:?\s*{numero}\s*(?:kilos?|kg|kilogramos?)',
        'temperatura_c': rf'(?:temperatura(?:\s+de)?)\s*:?\s*{numero}',
        'frecuencia_cardiaca': rf'(?:frecuencia card[ií]aca|pulso)\s*:?\s*{numero}',
        'frecuencia_respiratoria': rf'(?:frecuencia respiratoria)\s*:?\s*{numero}',
        'saturacion_oxigeno': rf'(?:saturaci[oó]n(?: de ox[ií]geno)?(?:\s+de)?)\s*:?\s*{numero}',
    }
    if campo in ('presion_sistolica', 'presion_diastolica'):
        pares = re.findall(rf'(?:presi[oó]n(?: arterial)?(?:\s+de)?)[^\d]{{0,10}}{numero}\s*(?:sobre|/|con)\s*{numero}', texto)
        if pares:
            indice = 0 if campo == 'presion_sistolica' else 1
            return len(pares) == 1 and float(pares[0][indice]) == valor
        etiqueta = 'sist[oó]lica' if campo == 'presion_sistolica' else 'diast[oó]lica'
        patron = rf'{etiqueta}\s*:?\s*{numero}'
    elif campo == 'talla_cm':
        palabras = {'cincuenta': 50, 'sesenta': 60, 'setenta': 70, 'ochenta': 80, 'noventa': 90}
        verbal = re.search(r'\bun metro (cincuenta|sesenta|setenta|ochenta|noventa)\b', texto)
        if verbal:
            return valor == 100 + palabras[verbal[1]]
        metros = re.search(rf'(?:mide|talla(?:\s+de)?)\s*:?\s*{numero}\s*(?:metros?|m)\b', texto)
        if metros:
            return math.isclose(float(metros[1]) * 100, valor)
        patron = rf'(?:mide|talla(?:\s+de)?)\s*:?\s*{numero}\s*(?:cm|cent[ií]metros?)'
    else:
        patron = patrones.get(campo)
    coincidencias = re.findall(patron, texto) if patron else []
    return len(coincidencias) == 1 and float(coincidencias[0]) == valor


def mediciones_explicitas(texto: str) -> list[Sugerencia]:
    """Complemento determinista del LLM, SOLO para medidas explícitas verificables."""
    inicios = [0] + [m.end() for m in FIN_FRASE.finditer(texto)]
    if inicios[-1] != len(texto):
        inicios.append(len(texto))
    encontradas = {}
    for inicio, fin in zip(inicios, inicios[1:]):
        frase = texto[inicio:fin].strip()
        if not frase or len(frase) > 3000:
            continue
        numeros = {float(n.replace(',', '.')) for n in re.findall(r'\d+(?:[.,]\d+)?', frase)}
        candidatos = numeros | {n * 100 for n in numeros} | {150, 160, 170, 180, 190}
        for campo in NUMERICOS:
            valores = [n for n in candidatos if numero_respaldado(campo, n, frase)]
            if len(valores) == 1:
                encontradas.setdefault(campo, []).append(Sugerencia(campo=campo, valor=valores[0], evidencia=frase))
    salida = []
    for items in encontradas.values():
        distintos = {item.valor for item in items}
        salida.append(items[0].model_copy(update={'ambiguo': len(distintos) > 1}))
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
    candidatos = [item for item in salida.campos if item.campo not in campos_medidos] + medidas
    vistos = set()
    for item in candidatos:
        if (item.campo == 'motivo_consulta'
                and re.search(r'\b(?:paciente presenta|paciente refiere)\b', item.evidencia, re.I)
                and re.search(r'\bniega\b', item.evidencia, re.I)
                and not re.search(r'\b(?:motivo|consulta por|viene por)\b', item.evidencia, re.I)):
            item = item.model_copy(update={'campo': 'sintomas'})
        if item.campo in vistos or item.evidencia not in transcripcion:
            resultado.advertencias.append(f'{item.campo}: evidencia ausente o propuesta repetida; no se aplicó.')
            continue
        vistos.add(item.campo)
        # No confiar en citas recortadas que omitan negación, dosis o una corrección posterior.
        posicion = transcripcion.index(item.evidencia)
        fin = posicion + len(item.evidencia)
        limites = list(FIN_FRASE.finditer(transcripcion))
        izquierda = max((m.end() for m in limites if m.end() <= posicion), default=0)
        derecha = min((m.end() for m in limites if m.end() >= fin), default=len(transcripcion))
        contexto = transcripcion[izquierda:derecha]
        if contexto.strip(' .!?\n\r\t') != item.evidencia.strip(' .!?\n\r\t'):
            resultado.advertencias.append(f'{item.campo}: la evidencia omitía parte de la frase; revisa el texto completo.')
            continue
        ambigua = item.ambiguo or bool(re.search(
            r'\?|\b(?:pregunta|creo|quiz[aá]s?|aproximadamente|cerca de|no se entiende|inaudible|no estoy seguro)\b', item.evidencia, re.I))
        if item.campo in ('diagnostico_principal', 'diagnosticos_secundarios') and re.search(
                r'\b(?:antecedentes?|hist[oó]rico|hace a[ñn]os)\b', item.evidencia, re.I):
            ambigua = True
        if item.campo in NUMERICOS and re.search(r'\b(?:ayer|antes|hist[oó]ric[oa]|niega|negad[oa])\b', item.evidencia, re.I):
            ambigua = True
        if item.campo in NUMERICOS:
            if isinstance(item.valor, str) or not numero_respaldado(item.campo, item.valor, item.evidencia):
                if (ambigua and not isinstance(item.valor, str) and math.isfinite(item.valor)
                        and item.valor > 0 and format(item.valor, 'g') in item.evidencia):
                    resultado.campos.append(item.model_copy(update={'ambiguo': True}))
                    continue
                resultado.advertencias.append(f'{item.campo}: medición o unidad no verificable; introdúcela manualmente.')
                continue
        elif not isinstance(item.valor, str) or item.valor != item.evidencia:
            resultado.advertencias.append(f'{item.campo}: el texto no era literal; revisa el original.')
            continue
        posicion = transcripcion.index(item.evidencia)
        inicio = max(transcripcion.rfind('.', 0, posicion), transcripcion.rfind('\n', 0, posicion)) + 1
        prefijo = transcripcion[inicio:posicion]
        if re.search(r'\b(?:niega|sin|no|posible|sospecha|descartar)\b', prefijo, re.I):
            resultado.advertencias.append(f'{item.campo}: evidencia recortada o contexto de negación; revisa el original.')
            continue
        resultado.campos.append(item.model_copy(update={'ambiguo': ambigua}))
    if any(item.ambiguo for item in resultado.campos):
        resultado.advertencias.append('Hay información ambigua. Revisa y resuelve esos campos manualmente.')
    return resultado
