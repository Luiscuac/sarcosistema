"""Inicializa el esquema de SarcoSistema en una base PostgreSQL nueva y dedicada."""

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.config.database import engine

RAIZ_BACKEND = Path(__file__).resolve().parents[1]
ESQUEMA = RAIZ_BACKEND.parent / "database" / "schema.sql"


def migrar(conexion):
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ_BACKEND / "alembic"))
    config.attributes["connection"] = conexion
    command.upgrade(config, "head")


async def inicializar():
    try:
        async with engine.begin() as conexion:
            await conexion.execute(text("SELECT pg_advisory_xact_lock(764290186173859604)"))
            elementos = await conexion.scalar(text("""
                SELECT (SELECT count(*) FROM pg_class WHERE relnamespace = 'public'::regnamespace)
                     + (SELECT count(*) FROM pg_proc WHERE pronamespace = 'public'::regnamespace)
                     + (SELECT count(*) FROM pg_type WHERE typnamespace = 'public'::regnamespace)
            """))
            if elementos:
                raise SystemExit("La base ya contiene objetos en public. Usa una base dedicada y vacía.")

            # asyncpg admite lotes SQL por su protocolo simple, sin preparar la sentencia.
            esquema = ESQUEMA.read_text(encoding="utf-8").replace(
                "SET client_encoding = 'SQL_ASCII';", "SET client_encoding = 'UTF8';",
            )
            driver = (await conexion.get_raw_connection()).driver_connection
            await driver.execute(esquema)
            await driver.execute("RESET ALL")
            await conexion.run_sync(migrar)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(inicializar())
    print("Esquema y migraciones aplicados a la base nueva.")
