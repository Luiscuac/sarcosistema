"""
Entidad Paciente: varios modulos la referencian (laboratorio, imagenes, accesos).
"""
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class Paciente(Base):
    __tablename__ = "paciente"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(50), nullable=True)
