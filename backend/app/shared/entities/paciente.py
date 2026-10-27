"""
Entidad Paciente: varios modulos la referencian (laboratorio, imagenes, accesos).
"""
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class Paciente(Base):
    __tablename__ = "paciente"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo_paciente: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    historia_clinica: Mapped[str | None] = mapped_column(Text, nullable=True)
    codigo_externo: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_documento: Mapped[str | None] = mapped_column(Text, nullable=True)
    numero_documento: Mapped[str | None] = mapped_column(Text, nullable=True)
    sin_documento: Mapped[bool] = mapped_column(Boolean, nullable=False)
    nombre_completo: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    sexo: Mapped[str] = mapped_column(Text, nullable=False)
    establecimiento_procedencia_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    estado: Mapped[str] = mapped_column(Text, nullable=False)
