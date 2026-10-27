"""
Conexion a PostgreSQL. Equivalente a database.config.ts
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings


class Base(DeclarativeBase):
    pass


# No activar ``echo``: SQLAlchemy también imprime los parámetros y podría
# exponer identificadores o datos clínicos en los logs del servidor.
engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    # Una transacción por operación HTTP; los repositorios solo hacen flush.
    async with SessionLocal.begin() as session:
        yield session
