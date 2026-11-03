"""Repositorio de corpus; la transacción pertenece al llamador."""
import json
import hashlib
from sqlalchemy import text

from app.imagenes.infrastructure.rag.embeddings import validar_vectores


class RepositorioRag:
    def __init__(self, session):
        self.session = session

    async def ingestar(self, documento: dict, fragmentos: list[dict], vectores: list[list[float]], modelo: str):
        validar_vectores(vectores)
        if not fragmentos or len(fragmentos) != len(vectores):
            raise ValueError('Fragmentos y embeddings incompatibles.')
        for f in fragmentos:
            if documento['contenido'][f['inicio']:f['fin']] != f['texto']:
                raise ValueError('Cita no corresponde al documento original.')
        existente = (await self.session.execute(text(
            'SELECT sha256,contenido FROM public.rag_torax_documento WHERE id=:id FOR UPDATE'),
            {'id': documento['id']})).mappings().first()
        if existente and (existente['sha256'] != documento['sha256'] or existente['contenido'] != documento['contenido']):
            raise ValueError('Documento existente incompatible; usar nueva versión, no sobrescribir.')
        await self.session.execute(text('''INSERT INTO public.rag_torax_documento
            (id,titulo,fuente,licencia,categoria,version,sha256,contenido)
            VALUES (:id,:titulo,:fuente,:licencia,:categoria,:version,:sha256,:contenido)
            ON CONFLICT (id) DO NOTHING'''), documento)
        for f, vector in zip(fragmentos, vectores):
            params = {**f, 'id': f['id'] + ':' + hashlib.sha256(modelo.encode()).hexdigest()[:16],
                      'documento_id': documento['id'], 'modelo': modelo, 'embedding': json.dumps(vector)}
            await self.session.execute(text('''INSERT INTO public.rag_torax_fragmento
                (id,documento_id,seccion,inicio,fin,texto,modelo,embedding)
                VALUES (:id,:documento_id,:seccion,:inicio,:fin,:texto,:modelo,CAST(:embedding AS vector))
                ON CONFLICT (id) DO NOTHING'''), params)

    async def buscar(self, vector: list[float], modelo: str, limite: int = 5) -> list[dict]:
        validar_vectores([vector])
        if not 1 <= limite <= 10:
            raise ValueError('Límite fuera del rango permitido.')
        rows = await self.session.execute(text('''SELECT f.id,f.documento_id,f.seccion,f.inicio,f.fin,f.texto,
            d.titulo,d.fuente,d.licencia,d.sha256,d.contenido,
            f.embedding <=> CAST(:embedding AS vector) AS distancia
            FROM public.rag_torax_fragmento f JOIN public.rag_torax_documento d ON d.id=f.documento_id
            WHERE f.modelo=:modelo
            ORDER BY distancia,f.id LIMIT :limite'''),
            {'embedding': json.dumps(vector), 'modelo': modelo, 'limite': limite})
        return [dict(row) for row in rows.mappings()]
