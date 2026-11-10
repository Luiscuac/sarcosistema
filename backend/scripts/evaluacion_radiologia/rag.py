"""Evalúa recuperación real y respuesta extractiva, sin LLM nuevo."""
import asyncio
import json
import time
from pathlib import Path
from scripts.evaluacion_radiologia.metricas import dividir


def medir_recuperacion(pregunta, recuperados):
    if not pregunta['respondible']:
        return {'recall_4': None, 'mrr': None}
    relevantes = {(r['documento_id'], r['seccion']) for r in pregunta['referencias']}
    encontrados = {(r['documento_id'], r['seccion']) for r in recuperados[:4]}
    rango = next((i for i, r in enumerate(recuperados, 1) if (r['documento_id'], r['seccion']) in relevantes), None)
    return {'recall_4': dividir(len(relevantes & encontrados), len(relevantes)),
            'mrr': 1/rango if rango else 0}


def verificar_cita(cita, documentos):
    d = documentos.get(cita['documento_id'])
    return bool(d and d['sha256'] == cita['sha256'] and
        0 <= cita['inicio'] < cita['fin'] <= len(d['contenido']) and
        d['contenido'][cita['inicio']:cita['fin']] == cita['cita'])


async def evaluar_lote(preguntas, vectores, buscar, documentos, checkpoint):
    from app.imagenes.application.consultar_rag import responder_con_evidencia
    if len(preguntas) != len(vectores):
        raise ValueError('Faltan vectores de preguntas')
    filas = []
    for p, vector in zip(preguntas, vectores):
        fila = {'id': p['id'], 'grupo': p['grupo'], 'respondible': p['respondible'], 'pregunta': p['pregunta']}
        inicio = time.perf_counter()
        try:
            recuperados = await buscar(vector)
            verificados = [e for e in recuperados if e['documento_id'] in documentos and
                e['sha256'] == documentos[e['documento_id']]['sha256'] and
                e['contenido'] == documentos[e['documento_id']]['contenido']]
            respuesta = responder_con_evidencia(p['pregunta'], verificados)
            fila.update({'retrieval': medir_recuperacion(p, verificados), 'respuesta': respuesta,
                'citas_validas': sum(verificar_cita(c, documentos) for c in respuesta['evidencia']),
                'abstiene': respuesta['estado'] == 'informacion_insuficiente',
                'sin_rag': {'estado': 'sin_evidencia_documental', 'evidencia': []},
                'ranking': [{'documento_id': e['documento_id'], 'seccion': e['seccion'], 'distancia': e['distancia']} for e in verificados]})
        except Exception as error:
            fila['error'] = type(error).__name__
        fila['retrieval_response_seconds'] = time.perf_counter()-inicio
        filas.append(fila)
        checkpoint(filas)
    return filas


async def evaluar_rag(preguntas, model_dir: Path, corpus_dir: Path, salida: Path):
    from app.imagenes.application.consultar_rag import responder_con_evidencia
    from app.imagenes.infrastructure.rag.embeddings import EmbeddingsLocales
    from app.imagenes.infrastructure.rag.ingesta import cargar_corpus
    from app.imagenes.infrastructure.rag.repository import RepositorioRag
    from app.config.database import SessionLocal, engine
    documentos = {d['id']: d for d, _ in cargar_corpus(corpus_dir)}
    manifest = json.loads((model_dir/'manifest.json').read_text(encoding='utf-8'))
    modelo = manifest['model']+'@'+manifest['revision']
    inicio = time.perf_counter()
    # Misma codificación local que producción, por lote para no reiniciar 40 hijos.
    generica = 'Radiografía de tórax: consolidación pulmonar, derrame pleural y cardiomegalia. Hallazgos radiográficos.'
    vectores = await asyncio.to_thread(EmbeddingsLocales(model_dir).codificar,
        [p['pregunta'] for p in preguntas]+[generica], True)
    embeddings_segundos = time.perf_counter()-inicio
    try:
        async def buscar(vector):
            async with SessionLocal() as db:
                return await RepositorioRag(db).buscar(vector, modelo, limite=10)
        def checkpoint(filas):
            salida.write_text(json.dumps({'n_intentos': len(filas), 'n_esperados': len(preguntas),
                'n_errores': sum('error' in f for f in filas), 'rows': filas}, ensure_ascii=False, indent=2), encoding='utf-8')
        filas = await evaluar_lote(preguntas, vectores[:-1], buscar, documentos, checkpoint)
        completas = [f for f in filas if 'error' not in f]
        respondibles = [f for f in completas if f['respondible']]
        noresp = [f for f in completas if not f['respondible']]
        abstienen = [f for f in completas if f['abstiene']]
        citas_n = sum(len(f['respuesta']['evidencia']) for f in completas)
        recuperados_generica = await buscar(vectores[-1])
        verificados_generica = [e for e in recuperados_generica if e['documento_id'] in documentos and
            e['sha256'] == documentos[e['documento_id']]['sha256'] and e['contenido'] == documentos[e['documento_id']]['contenido']]
        r = {'n': len(filas), 'n_esperados': len(preguntas), 'n_completados': len(completas),
            'n_errores': len(filas)-len(completas), 'n_respondibles': len(respondibles), 'n_no_respondibles': len(noresp),
            'cobertura_sobre_total': dividir(sum(bool(f['respuesta']['evidencia']) for f in completas), len(preguntas)),
            'recall_4': dividir(sum(f['retrieval']['recall_4'] for f in respondibles), len(respondibles)),
            'mrr_10': dividir(sum(f['retrieval']['mrr'] for f in respondibles), len(respondibles)),
            'abstencion_precision': dividir(sum(not f['respondible'] for f in abstienen), len(abstienen)),
            'abstencion_recall': dividir(sum(f['abstiene'] for f in noresp), len(noresp)),
            'citas_n': citas_n, 'citas_integras': dividir(sum(f['citas_validas'] for f in completas), citas_n),
            'cobertura_respondibles': dividir(sum(bool(f['respuesta']['evidencia']) for f in respondibles), len(respondibles)),
            'embeddings_batch_seconds': embeddings_segundos, 'model': modelo, 'rows': filas,
            'consulta_fija_integracion': responder_con_evidencia(generica, verificados_generica)}
        salida.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
        return r
    finally:
        await engine.dispose()
