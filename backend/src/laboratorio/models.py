"""
Entidades SQLAlchemy del modulo laboratorio.
Equivalente a examen.entity.ts en el diagrama original: define la tabla.
"""
from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class Examen(Base):
    __tablename__ = "examen"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("paciente.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="pendiente_muestra")
