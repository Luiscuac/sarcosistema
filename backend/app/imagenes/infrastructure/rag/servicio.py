import asyncio
import json
from pathlib import Path

from app.imagenes.application.consultar_rag import responder_con_evidencia
from app.imagenes.infrastructure.rag.embeddings import EmbeddingsLocales
from app.imagenes.infrastructure.rag.ingesta import cargar_corpus
from app.imagenes.infrastructure.rag.repository import RepositorioRag


class ServicioRag:
    def __init__(self, model_dir: Path, corpus_dir: Path, sesiones):
        self.model_dir,self.corpus_dir,self.sesiones = model_dir,corpus_dir,sesiones

    async def consultar(self, pregunta: str):
        corpus = await asyncio.to_thread(cargar_corpus,self.corpus_dir)
        manifest = json.loads((self.model_dir/'manifest.json').read_text(encoding='utf-8'))
        modelo = manifest['model']+'@'+manifest['revision']
        vector = (await asyncio.to_thread(EmbeddingsLocales(self.model_dir).codificar,[pregunta],True))[0]
        async with self.sesiones() as session:
            recuperados = await RepositorioRag(session).buscar(vector,modelo,limite=10)
        documentos = {d['id']:d for d,_ in corpus}
        verificados = [e for e in recuperados if e['documento_id'] in documentos
            and e['sha256']==documentos[e['documento_id']]['sha256']
            and e['contenido']==documentos[e['documento_id']]['contenido']]
        return responder_con_evidencia(pregunta,verificados)
