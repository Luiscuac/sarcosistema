"""Prueba optativa real; red Docker interna, modelo y corpus readonly."""
import os
import socket
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.getenv('RUN_RAG_OFFLINE_TESTS') != '1', reason='Requiere entorno RAG aislado preparado')


def test_sin_salida_a_internet_real():
    with pytest.raises(OSError):
        socket.create_connection(('1.1.1.1', 443), timeout=2)


@pytest.mark.asyncio
async def test_pgvector_embeddings_citas_y_abstencion_offline():
    import importlib.util
    import json
    from argparse import Namespace
    from sqlalchemy.ext.asyncio import create_async_engine
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from scripts.consultar_rag_torax import ejecutar
    spec = importlib.util.spec_from_file_location('migration_rag', '/app/migration_rag.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.begin() as connection:
        def migrar(conn):
            with Operations.context(MigrationContext.configure(conn)):
                module.upgrade()
        await connection.run_sync(migrar)
    await engine.dispose()
    args = Namespace(corpus_dir=Path('/corpus'), model_dir=Path('/models'), min_free_mib=1536,
                     indexar=True, pregunta=None)
    assert (await ejecutar(args))['documentos'] == 2
    args.indexar = False
    resultados = []
    for pregunta in ('¿Qué signos radiográficos puede tener el derrame pleural?',
                     '¿Qué limitaciones tiene la radiografía de tórax?',
                     '¿Cómo reparar un motor de automóvil?'):
        args.pregunta = pregunta
        r = await ejecutar(args)
        resultados.append(r)
        if 'automóvil' in pregunta:
            assert r['estado'] == 'informacion_insuficiente'
        elif 'limitaciones' in pregunta:
            # El corpus recuperado puede ser insuficiente: no exigir evidencia
            # aparente a costa de aceptar sensibilidad de CT/biopsia como RX.
            assert r['estado'] == 'informacion_insuficiente'
            assert r['evidencia'] == []
        else:
            assert r['estado'] == 'evidencia_recuperada', r
            assert all(e['cita'] and e['fuente'].startswith('https://pmc.ncbi.nlm.nih.gov/') for e in r['evidencia'])
    print('RAG_OFFLINE_RESULTADOS=' + json.dumps(resultados, ensure_ascii=True))
