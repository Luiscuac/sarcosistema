"""Modelos ORM de estudios de imagen (informes y archivos clinicos)."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class InformeImagen(Base):
    """Informe versionado de un estudio de imagen; solo el publicado ve el medico."""

    __tablename__ = "informe_imagen"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    estudio_id: Mapped[int] = mapped_column(ForeignKey("estudio_solicitado.id"), nullable=False)
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion_texto: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    motivo_rectificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    usuario_publicacion_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    fecha_hora_publicacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version_anterior_id: Mapped[int | None] = mapped_column(
        ForeignKey("informe_imagen.id"), nullable=True
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)


class ArchivoImagen(Base):
    """Metadatos de un archivo clinico; el binario vive fuera de la base."""

    __tablename__ = "archivo_imagen"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    informe_id: Mapped[int] = mapped_column(ForeignKey("informe_imagen.id"), nullable=False)
    nombre_original: Mapped[str] = mapped_column(Text, nullable=False)
    url_archivo: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_carga: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    motivo_retiro: Mapped[str | None] = mapped_column(Text, nullable=True)
    archivo_reemplazado_id: Mapped[int | None] = mapped_column(
        ForeignKey("archivo_imagen.id"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
