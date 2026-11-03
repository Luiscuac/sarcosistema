"""Constancias de muestras que no pudieron recibirse o tomarse."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class IncidenciaMuestra(Base):
    __tablename__ = "incidencia_muestra"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    estudio_id: Mapped[int] = mapped_column(ForeignKey("estudio_solicitado.id"), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    responsable: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
