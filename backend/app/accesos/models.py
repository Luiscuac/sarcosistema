"""
Entidades SQLAlchemy del modulo accesos.
Mapeo de la tabla 'usuario' existente en la BD (schema.sql lineas 1801-1811).
"""
from sqlalchemy import BigInteger, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    identificador_acceso: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    contrasena_hash: Mapped[str] = mapped_column(Text, nullable=False)
    rol_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    trabajador_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    estado: Mapped[str] = mapped_column(Text, nullable=False)


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
