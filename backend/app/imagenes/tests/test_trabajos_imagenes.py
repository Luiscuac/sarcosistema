from contextlib import asynccontextmanager

import pytest

from app.imagenes.infrastructure.trabajos import ejecutar_trabajo


class Sesiones:
    @asynccontextmanager
    async def begin(self):
        yield object()


@pytest.mark.asyncio
async def test_trabajo_sanea_error_no_persiste_detalles_internos():
    guardados = []
    class Repo:
        def __init__(self, _):
            pass
        async def obtener(self,*_):
            raise RuntimeError('fixture secreto no debe aparecer')
        async def finalizar(self,*args):
            guardados.append(args)
    await ejecutar_trabajo({'id':'test','estudio_id':1,'solicitado_por':2},Sesiones(),None,Repo)
    assert guardados == [('test',None,'fallo_local')]


@pytest.mark.asyncio
async def test_snapshot_no_disponible_no_ejecuta_modelo():
    guardados = []
    class Repo:
        def __init__(self, _):
            pass
        async def obtener(self,*_):
            return None
        async def finalizar(self,*args):
            guardados.append(args)
    class Analizador:
        async def ejecutar(self,*_):
            pytest.fail('No debe ejecutar modelo para snapshot inexistente')
    await ejecutar_trabajo({'id':'test','estudio_id':1,'solicitado_por':2},Sesiones(),Analizador(),Repo)
    assert guardados == [('test',None,'snapshot_obsoleto')]


@pytest.mark.asyncio
async def test_perder_liderazgo_impide_leer_o_finalizar_otro_trabajo():
    class Repo:
        def __init__(self,_):
            pytest.fail('Un antiguo líder no debe consultar ni finalizar trabajos')
    async def no_vigente():
        return False
    await ejecutar_trabajo({'id':'test'},Sesiones(),None,Repo,vigente=no_vigente)


@pytest.mark.asyncio
async def test_detecta_fin_de_su_propia_conexion_lider_en_postgresql():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    from app.config.settings import settings
    from app.imagenes.infrastructure.trabajos import Liderazgo
    engine = create_async_engine(settings.database_url,poolclass=NullPool)
    async with engine.connect() as conn:
        adquirido = await conn.scalar(text('SELECT pg_try_advisory_lock(2111009)'))
        await conn.commit()
        if not adquirido:
            pytest.skip('Otro ejecutor posee el liderazgo; no se interrumpe su trabajo')
        datos = (await conn.execute(text('SELECT pid,backend_start AS inicio FROM pg_stat_activity WHERE pid=pg_backend_pid()'))).mappings().one()
        await conn.commit()
        liderazgo = Liderazgo(conn,dict(datos))
        assert await liderazgo.comprobar()
        async with engine.begin() as otra:
            # Solo termina la conexión que ESTA prueba acaba de crear y bloquear.
            await otra.execute(text('SELECT pg_terminate_backend(:pid)'),{'pid':datos['pid']})
        assert not await liderazgo.comprobar()
        assert await liderazgo.reclamar() is None
    await engine.dispose()
