"""Modelos ORM del flujo muestras de laboratorio."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

class Muestra(Base):
    __tablename__ = "muestra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    referencia_muestra: Mapped[str] = mapped_column(Text, nullable=False)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("paciente.id"), nullable=False)
    fecha_toma_real: Mapped[date] = mapped_column(Date, nullable=False)
    hora_toma_real: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_no_registrada: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fecha_hora_ingreso_sistema: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    tipo_muestra: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)

class MuestraEstudio(Base):
    __tablename__ = "muestra_estudio"

    muestra_id: Mapped[int] = mapped_column(ForeignKey("muestra.id"), primary_key=True)
    estudio_id: Mapped[int] = mapped_column(
        ForeignKey("estudio_solicitado.id"), primary_key=True
    )
