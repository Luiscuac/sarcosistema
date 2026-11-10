"""Ablación contractual: visión sintética y replay documental explícitos.

NO sustituye el flujo API con modelos reales, que se ejecuta por separado.
"""
import hashlib
import time
from app.imagenes.application.analizar_estudio import AnalizarEstudio
from scripts.evaluacion_radiologia.casos import TERMINOS


async def evaluar_ablacion(casos, evidencia_generica):
    class VisionControlada:
        def analizar(self, contenido, **kwargs):
            return {'synthetic': True, 'findings': [{'name': k, 'score': .8} for k in TERMINOS]}

    class RagReplay:
        def __init__(self, salida):
            self.salida = salida
            self.preguntas = []

        async def consultar(self, pregunta):
            self.preguntas.append(pregunta)
            return self.salida

    con = RagReplay(evidencia_generica)
    sin = RagReplay({'estado': 'deshabilitado_evaluacion', 'evidencia': []})
    filas = []
    for c in casos:
        snapshot = {'id': 1, 'informe_id': 1, 'informe_texto': c['informe'],
                    'archivo': {'id': 1, 'hash_sha256': 'control-sintetico'}}
        trabajo = {'estudio_id': 1, 'informe_id': 1, 'archivo_id': 1,
            'informe_sha256': hashlib.sha256(c['informe'].encode()).hexdigest(),
            'archivo_sha256': 'control-sintetico', 'informe_texto': c['informe'], 'proyeccion': 'PA'}
        resultados = []
        inicio = time.perf_counter()
        for rag in (sin, con):
            resultados.append(await AnalizarEstudio(VisionControlada(), rag, lambda _: b'control').ejecutar(trabajo, snapshot))
        a, b = resultados
        filas.append({'id': c['id'], 'scores_identicos': a['vision'] == b['vision'],
            'fusion_identica': a['fusion'] == b['fusion'],
            'confirmaciones': len(a['fusion']['hallazgos_confirmados']) + len(b['fusion']['hallazgos_confirmados']),
            'sin_rag_citas': len(a['rag']['evidencia']), 'con_rag_citas': len(b['rag']['evidencia']),
            'tiempo_contrato_replay_par_seconds': time.perf_counter()-inicio})
    return {'n_pares': len(filas), 'vision_synthetic': True, 'rag_replay': True,
        'fuente_rag': 'Respuesta real a consulta fija reutilizada; no 300 recuperaciones independientes',
        'scores_identicos': sum(f['scores_identicos'] for f in filas),
        'fusion_identica': sum(f['fusion_identica'] for f in filas),
        'confirmaciones': sum(f['confirmaciones'] for f in filas),
        'consultas_distintas': len(set(con.preguntas)), 'rows': filas}
