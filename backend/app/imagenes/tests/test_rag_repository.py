import pytest

from app.imagenes.infrastructure.rag.repository import RepositorioRag
import os


@pytest.mark.asyncio
async def test_busqueda_rechaza_dimension_antes_de_acceder_bd():
    with pytest.raises(ValueError):
        await RepositorioRag(None).buscar([1.] * 3, 'model-v1')


@pytest.mark.asyncio
async def test_busqueda_limita_resultados():
    with pytest.raises(ValueError):
        await RepositorioRag(None).buscar([1.] + [0.] * 383, 'model-v1', limite=1000)


@pytest.mark.asyncio
@pytest.mark.skipif(os.getenv('RUN_RAG_DB_TESTS') != '1', reason='Requiere PostgreSQL migrado explícitamente')
async def test_pgvector_real_ingesta_idempotente_busqueda_y_cita():
    from app.config.database import engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import text
    import hashlib
    import uuid
    id = 'TEST-RAG-' + uuid.uuid4().hex
    contenido = 'Ficticio: evidencia de integración, no fuente médica.'
    documento = dict(id=id, titulo='Prueba sintética', fuente='synthetic:test', licencia='synthetic',
                     categoria='test', version='1', sha256=hashlib.sha256(contenido.encode()).hexdigest(), contenido=contenido)
    fragmentos = [dict(id=id+'-0', seccion='Prueba', inicio=0, fin=len(contenido), texto=contenido)]
    vector = [1.] + [0.] * 383
    async with engine.connect() as conn:
        transaction = await conn.begin()
        try:
            async with AsyncSession(bind=conn) as session:
                repo = RepositorioRag(session)
                await repo.ingestar(documento, fragmentos, [vector], id)
                await repo.ingestar(documento, fragmentos, [vector], id)
                rows = await repo.buscar(vector, id)
                assert len(rows) == 1
                assert rows[0]['texto'] == contenido
                assert rows[0]['distancia'] == pytest.approx(0.)
                assert await session.scalar(text('SELECT count(*) FROM public.rag_torax_fragmento WHERE documento_id=:id'), {'id':id}) == 1
        finally:
            await transaction.rollback()
