"""Modelos ORM del flujo solicitudes de laboratorio."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

class Solicitud(Base):
    __tablename__ = "solicitud"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    referencia: Mapped[str] = mapped_column(Text, nullable=False)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("paciente.id"), nullable=False)
    referencia_papel_formulario: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    establecimiento_solicitante_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    establecimiento_solicitante_nombre_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    medico_solicitante_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    medico_solicitante_nombre_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostico_principal: Mapped[str | None] = mapped_column(Text, nullable=True)
    prioridad: Mapped[str] = mapped_column(Text, nullable=False)
    clave_idempotencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)

class EstudioSolicitado(Base):
    __tablename__ = "estudio_solicitado"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    referencia: Mapped[str] = mapped_column(Text, nullable=False)
    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitud.id"), nullable=False)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("paciente.id"), nullable=False)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicio.id"), nullable=False)
    tipo_estudio_id: Mapped[int] = mapped_column(ForeignKey("tipo_estudio.id"), nullable=False)
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)

class EstudioEstadoHistorial(Base):
    __tablename__ = "estudio_estado_historial"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    estudio_id: Mapped[int] = mapped_column(
        ForeignKey("estudio_solicitado.id"), nullable=False
    )
    estado_anterior: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(Text, nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
