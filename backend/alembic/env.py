"""
Entorno de Alembic: migraciones versionadas, como pide la seccion de
mantenimiento (cambios de tablas y columnas con respaldo antes de aplicar).
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.database import Base
from app.config.settings import settings

# Importar aca todos los modulos con modelos para que Alembic los detecte:
from app.accesos.infrastructure.persistence.models import usuario as _usuario_model  # noqa: F401
from app.laboratorio.infrastructure.persistence import models as _laboratorio_models  # noqa: F401
from app.shared.entities import paciente as _paciente_models  # noqa: F401

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def incluir_objeto(objeto, nombre, tipo, reflejado, comparar_con):
    """Evita que el autogenerate proponga borrar partes del esquema no mapeadas."""
    if reflejado and comparar_con is None:
        return False
    return True


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        include_schemas=True,
        include_object=incluir_objeto,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        def ejecutar_migraciones(sync_conn):
            context.configure(
                connection=sync_conn,
                target_metadata=target_metadata,
                include_schemas=True,
                include_object=incluir_objeto,
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(ejecutar_migraciones)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
