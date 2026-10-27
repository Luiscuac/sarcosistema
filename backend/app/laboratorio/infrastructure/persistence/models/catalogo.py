"""Modelos ORM del flujo catalogo de laboratorio."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

class Servicio(Base):
    __tablename__ = "servicio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class TipoEstudio(Base):
    __tablename__ = "tipo_estudio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicio.id"), nullable=False)
    requiere_muestra: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requiere_informe: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requiere_archivos: Mapped[bool] = mapped_column(Boolean, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False)
    plantilla_examen_id: Mapped[int | None] = mapped_column(
        ForeignKey("plantilla_examen.id", ondelete="RESTRICT"), nullable=True
    )
    categoria_laboratorio: Mapped[str | None] = mapped_column(Text, nullable=True)
