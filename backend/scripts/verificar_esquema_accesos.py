"""Comprueba solo la estructura de identidad de la base configurada."""
import asyncio

from sqlalchemy import text

from app.config.database import engine


async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('usuario', 'rol', 'trabajador')
            ORDER BY table_name, ordinal_position
        """))
        for table_name, column_name in result:
            print(f"{table_name}.{column_name}")


if __name__ == "__main__":
    asyncio.run(main())
