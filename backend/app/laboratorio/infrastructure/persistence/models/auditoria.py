"""Modelos ORM del flujo auditoria de laboratorio."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


from app.accesos.infrastructure.persistence.models.usuario import Usuario as _UsuarioModel  # noqa: F401

class AuditoriaAccion(Base):
    __tablename__ = "auditoria_accion"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    entidad_afectada: Mapped[str] = mapped_column(Text, nullable=False)
    referencia_registro: Mapped[str | None] = mapped_column(Text, nullable=True)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
