"""Modelos ORM del flujo plantillas de laboratorio."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

class PlantillaExamen(Base):
    __tablename__ = "plantilla_examen"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicio.id"), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False)

class PlantillaExamenVersion(Base):
    __tablename__ = "plantilla_examen_version"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plantilla_examen_id: Mapped[int] = mapped_column(
        ForeignKey("plantilla_examen.id"), nullable=False
    )
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class SeccionPlantilla(Base):
    __tablename__ = "seccion_plantilla"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plantilla_version_id: Mapped[int] = mapped_column(
        ForeignKey("plantilla_examen_version.id"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)

class ParametroPlantilla(Base):
    __tablename__ = "parametro_plantilla"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plantilla_version_id: Mapped[int] = mapped_column(
        ForeignKey("plantilla_examen_version.id"), nullable=False
    )
    seccion_id: Mapped[int | None] = mapped_column(
        ForeignKey("seccion_plantilla.id"), nullable=True
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_entrada: Mapped[str] = mapped_column(Text, nullable=False)
    unidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    rango_referencia_texto: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_minimo: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    valor_maximo: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    obligatorio: Mapped[bool] = mapped_column(Boolean, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    precision_decimal: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

class OpcionParametro(Base):
    __tablename__ = "opcion_parametro"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    parametro_id: Mapped[int] = mapped_column(
        ForeignKey("parametro_plantilla.id", ondelete="RESTRICT"), nullable=False
    )
    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    etiqueta: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False)
