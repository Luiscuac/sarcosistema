"""Fase5 reproducible: modelos existentes, sin entrenamiento ni descargas."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import platform
import time
import socket

BASE = Path(__file__).resolve().parents[1]


def guardar(path, datos):
    path.write_text(json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entradas', type=Path, default=BASE.parent/'docs/imagenes/evaluacion')
    parser.add_argument('--salida', type=Path, default=BASE/'.radiologia-resultados/fase5')
    parser.add_argument('--muestras', type=Path, default=BASE/'.datasets/evaluacion-fase5/muestras.json')
    parser.add_argument('--visual', action='store_true')
    parser.add_argument('--rag', action='store_true')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    import psutil
    inicio = time.perf_counter()
    if args.offline:
        try:
            socket.create_connection(('1.1.1.1', 443), timeout=2).close()
        except OSError:
            pass
        else:
            raise RuntimeError('Salida externa accesible, no es ejecución offline')
    entradas = args.entradas/'casos-sinteticos.jsonl'
    casos = [json.loads(l) for l in entradas.read_text(encoding='utf-8').splitlines()]
    from scripts.evaluacion_radiologia.texto import evaluar_textos
    texto = evaluar_textos(casos); guardar(args.salida/'texto.json', texto)
    resultado = {'python': platform.python_version(), 'platform': platform.platform(),
        'cpu': platform.processor(), 'cpu_logical': psutil.cpu_count(),
        'ram_total_bytes': psutil.virtual_memory().total, 'ram_available_bytes_inicio': psutil.virtual_memory().available,
        'offline_external_socket_blocked': args.offline,
        'corpus_sha256': hashlib.sha256(entradas.read_bytes()).hexdigest(),
        'n_textos': len(casos), 'exactitud_objetivo': texto['objetivo']['exactitud']}
    if args.visual:
        from scripts.evaluacion_radiologia.visual import evaluar_visual
        r = evaluar_visual(args.muestras, BASE/'.models/radiologia', args.salida/'visual.json')
        resultado['visual_completados'] = r['n_completados']
    if args.rag:
        from scripts.evaluacion_radiologia.rag import evaluar_rag
        preguntas = json.loads((args.entradas/'preguntas-rag.json').read_text(encoding='utf-8'))
        r = asyncio.run(evaluar_rag(preguntas, BASE/'.models/rag-torax', BASE/'.datasets/rag-torax', args.salida/'rag.json'))
        from scripts.evaluacion_radiologia.integracion import evaluar_ablacion
        guardar(args.salida/'ablacion.json', asyncio.run(evaluar_ablacion(casos, r['consulta_fija_integracion'])))
        resultado['rag_n'] = r['n']
    resultado['total_seconds'] = time.perf_counter()-inicio
    guardar(args.salida/'ejecucion.json', resultado)
    print(json.dumps(resultado, ensure_ascii=True))


if __name__ == '__main__':
    main()
