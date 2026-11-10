"""Actualiza historiales de imágenes sin stamp ni reescribir versiones aplicadas.

Usar primero en una copia aislada. Por defecto solo muestra las revisiones.
--aplicar completa la unión histórica si hay dos ramas originales y después
ejecuta upgrade head. No descarga modelos ni cambia credenciales.
"""
import argparse
import asyncio
from pathlib import Path
import shutil
import tempfile

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool


async def revisiones(url):
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            if not await conn.scalar(text("SELECT to_regclass('public.alembic_version') IS NOT NULL")):
                return ()
            return tuple((await conn.execute(text('SELECT version_num FROM public.alembic_version ORDER BY version_num'))).scalars())
    finally:
        await engine.dispose()


def actualizar_conexion(config, conexion):
    existe = conexion.scalar(text("SELECT to_regclass('public.alembic_version') IS NOT NULL"))
    actuales = tuple(conexion.execute(text('SELECT version_num FROM public.alembic_version ORDER BY version_num')).scalars()) if existe else ()
    if len(actuales) > 1:
        ia = {'20261103_0008', '20261103_0009'}
        lab = {'20261102_0008', '20261102_0009', '20261102_0010', '20261103_0011'}
        if len(actuales) != 2 or len(set(actuales) & ia) != 1 or len(set(actuales) & lab) != 1:
            raise RuntimeError('Historial múltiple no reconocido; revisar metadatos en copia aislada.')
        # Recuperar SOLO en copia temporal el grafo original distribuido. El DDL
        # y DML son los mismos archivos históricos, sin edición de sus cuerpos.
        temporal = Path.home() / 'AppData/Local/Temp/opencode'
        with tempfile.TemporaryDirectory(prefix='sarco-historial-original-', dir=temporal if temporal.exists() else None) as carpeta:
            destino = Path(carpeta) / 'alembic'
            shutil.copytree(config.get_main_option('script_location'), destino,
                            ignore=shutil.ignore_patterns('__pycache__'))
            for ruta in (destino / 'versions').glob('*.py'):
                if ruta.name.startswith(('20261104_0012', '20261109_0013')):
                    ruta.unlink()
            ruta = destino / 'versions/20261103_0008_rag_torax.py'
            contenido = ruta.read_text(encoding='utf-8')
            if "down_revision = '20261104_0012'" not in contenido:
                raise RuntimeError('El grafo distribuido cambió; detener y revisar la reconciliación.')
            ruta.write_text(contenido.replace("down_revision = '20261104_0012'",
                                             "down_revision = '20261027_0007'"), encoding='utf-8')
            original = Config(config.config_file_name)
            original.set_main_option('script_location', str(destino))
            original.set_main_option('sqlalchemy.url', config.get_main_option('sqlalchemy.url').replace('%', '%%'))
            original.attributes['connection'] = conexion
            command.upgrade(original, '20261109_0012')
    anterior = config.attributes.get('connection')
    config.attributes['connection'] = conexion
    try:
        command.upgrade(config, 'head')
    finally:
        if anterior is None:
            config.attributes.pop('connection', None)
        else:
            config.attributes['connection'] = anterior


async def actualizar_transaccion(config):
    engine = create_async_engine(config.get_main_option('sqlalchemy.url'), poolclass=NullPool)
    try:
        async with engine.begin() as conexion:
            await conexion.run_sync(lambda sync: actualizar_conexion(config, sync))
    finally:
        await engine.dispose()


def actualizar(config):
    """Inspección y dos upgrades sobre el mismo destino y transacción reales."""
    asyncio.run(actualizar_transaccion(config))


def main():
    from app.config.settings import settings
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aplicar', action='store_true')
    args = parser.parse_args()
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    config.set_main_option('script_location', str(Path(__file__).resolve().parents[1] / 'alembic'))
    config.set_main_option('sqlalchemy.url', settings.database_url.replace('%', '%%'))
    print('Revisiones registradas:', ', '.join(asyncio.run(revisiones(settings.database_url))) or '(ninguna)')
    if args.aplicar:
        actualizar(config)
        print('Actualización completada. Verificar contrato físico y flujos antes de habilitar el servicio.')
    else:
        print('Solo lectura. Probar y revisar el plan en copia aislada antes de usar --aplicar.')


if __name__ == '__main__':
    main()
