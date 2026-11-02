"""Modelos ORM del flujo resultados de laboratorio."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

class ResultadoLaboratorio(Base):
    __tablename__ = "resultado_laboratorio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    estudio_id: Mapped[int] = mapped_column(ForeignKey("estudio_solicitado.id"), nullable=False)
    plantilla_version_id: Mapped[int] = mapped_column(
        ForeignKey("plantilla_examen_version.id"), nullable=False
    )
    observaciones_generales: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)

class VersionResultado(Base):
    __tablename__ = "version_resultado"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    resultado_id: Mapped[int] = mapped_column(
        ForeignKey("resultado_laboratorio.id"), nullable=False
    )
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    motivo_rectificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    usuario_publicacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id"), nullable=True
    )
    fecha_hora_publicacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)

class DetalleValorResultado(Base):
    __tablename__ = "detalle_valor_resultado"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    version_resultado_id: Mapped[int] = mapped_column(
        ForeignKey("version_resultado.id"), nullable=False
    )
    parametro_id: Mapped[int] = mapped_column(
        ForeignKey("parametro_plantilla.id"), nullable=False
    )
    valor_entero: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valor_decimal: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    valor_texto: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_cualitativo: Mapped[str | None] = mapped_column(Text, nullable=True)
    fuera_de_rango: Mapped[bool] = mapped_column(Boolean, nullable=False)
