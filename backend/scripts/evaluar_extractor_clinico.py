"""Evalúa el extractor clínico local con dictados ficticios y resume los aciertos.

Uso, desde backend/ con Ollama iniciado:
    python -m scripts.evaluar_extractor_clinico --modelo qwen2.5:3b --salida resultados.json

No guarda nada en la base de datos ni envía texto fuera del equipo (Ollama en loopback).
"""
import argparse
import asyncio
import json
import time
import unicodedata
from pathlib import Path

from app.consultas.application.ports.extractor_clinico import ErrorExtractor
from app.consultas.infrastructure.ia.ollama import OllamaExtractor
from scripts.casos_extractor_clinico import CASOS

NEGACIONES = ('no ', 'niega', 'sin ', 'ni ', 'negativ', 'ausencia')


def normalizar(texto) -> str:
    sin_tildes = unicodedata.normalize('NFD', str(texto).lower())
    return ''.join(letra for letra in sin_tildes if unicodedata.category(letra) != 'Mn')


def evaluar_caso(caso: dict, propuesta) -> list[tuple[str, bool]]:
    """Devuelve (descripción, aprobado) por cada comprobación del caso."""
    campos = {item.campo: item for item in propuesta.campos}
    texto = {campo: normalizar(item.valor) for campo, item in campos.items()}
    comprobaciones = []

    if caso.get('bloqueada'):
        comprobaciones.append(('bloquea varios pacientes', propuesta.bloqueada and not campos))
        return comprobaciones
    comprobaciones.append(('no bloquea un dictado válido', not propuesta.bloqueada))

    for campo, palabras in caso.get('contiene', {}).items():
        presentes = campo in texto and all(normalizar(p) in texto[campo] for p in palabras)
        comprobaciones.append((f'{campo} contiene {palabras}', presentes))
    for campo, esperado in caso.get('numeros', {}).items():
        valor = campos[campo].valor if campo in campos else None
        correcto = isinstance(valor, (int, float)) and abs(valor - esperado) < 0.01
        comprobaciones.append((f'{campo} = {esperado} (obtuvo {valor})', correcto))
    for campo, palabras in caso.get('no_contiene', {}).items():
        limpio = campo not in texto or not any(normalizar(p) in f' {texto[campo]}' for p in palabras)
        comprobaciones.append((f'{campo} no agrega {palabras}', limpio))
    for campo, palabras in caso.get('negados', {}).items():
        valor = texto.get(campo, '')
        conserva = all(normalizar(p) not in valor or any(n in f' {valor}' for n in NEGACIONES) for p in palabras)
        comprobaciones.append((f'{campo} conserva negación de {palabras}', conserva))
    for campo in caso.get('ausentes', []):
        comprobaciones.append((f'{campo} no se propone', campo not in campos))
    if caso.get('solo'):
        esperados = set(caso.get('contiene', {})) | set(caso.get('numeros', {}))
        extra = set(campos) - esperados
        comprobaciones.append((f'sin campos inventados (extra: {sorted(extra)})', not extra))
    return comprobaciones


async def evaluar(modelo: str, timeout: int) -> dict:
    extractor = OllamaExtractor(modelo=modelo, timeout=timeout)
    resultados = []
    for caso in CASOS:
        inicio = time.perf_counter()
        try:
            propuesta = await extractor.extraer(caso['texto'])
            comprobaciones = evaluar_caso(caso, propuesta)
            error = None
            detalle = [{'campo': c.campo, 'valor': c.valor, 'evidencia': c.evidencia, 'ambiguo': c.ambiguo,
                        'alertas': getattr(c, 'alertas', [])} for c in propuesta.campos]
            advertencias = propuesta.advertencias
        except ErrorExtractor as exc:
            comprobaciones, error, detalle, advertencias = [('el extractor respondió', False)], str(exc), [], []
        segundos = round(time.perf_counter() - inicio, 1)
        aprobadas = sum(ok for _, ok in comprobaciones)
        print(f"{caso['nombre']:<32} {aprobadas:>2}/{len(comprobaciones):<2} {segundos:>6}s")
        for descripcion, ok in comprobaciones:
            if not ok:
                print(f'    ✗ {descripcion}')
        resultados.append({'caso': caso['nombre'], 'aprobadas': aprobadas, 'total': len(comprobaciones),
                           'segundos': segundos, 'error': error, 'fallos': [d for d, ok in comprobaciones if not ok],
                           'campos': detalle, 'advertencias': advertencias})
    aprobadas = sum(r['aprobadas'] for r in resultados)
    total = sum(r['total'] for r in resultados)
    tiempo = round(sum(r['segundos'] for r in resultados) / len(resultados), 1)
    print(f'\nTOTAL {aprobadas}/{total} comprobaciones ({aprobadas / total:.0%}) · promedio {tiempo}s por dictado')
    return {'modelo': modelo, 'aprobadas': aprobadas, 'total': total, 'segundos_promedio': tiempo, 'casos': resultados}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', default='qwen2.5:3b')
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--salida', type=Path)
    argumentos = parser.parse_args()
    resumen = asyncio.run(evaluar(argumentos.modelo, argumentos.timeout))
    if argumentos.salida:
        argumentos.salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


if __name__ == '__main__':
    main()
