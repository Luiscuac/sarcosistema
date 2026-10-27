"""Mapeo ORM de las tablas de laboratorio ya presentes en schema.sql."""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.accesos.infrastructure.persistence.models.usuario import Usuario as _UsuarioModel  # noqa: F401
from app.config.database import Base


class Servicio(Base):
    __tablename__ = "servicio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TipoEstudio(Base):
    __tablename__ = "tipo_estudio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicio.id"), nullable=False)
    requiere_muestra: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requiere_informe: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requiere_archivos: Mapped[bool] = mapped_column(Boolean, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False)
    plantilla_examen_id: Mapped[int | None] = mapped_column(
        ForeignKey("plantilla_examen.id", ondelete="RESTRICT"), nullable=True
    )
    categoria_laboratorio: Mapped[str | None] = mapped_column(Text, nullable=True)


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


class MuestraEstudio(Base):
    __tablename__ = "muestra_estudio"

    muestra_id: Mapped[int] = mapped_column(ForeignKey("muestra.id"), primary_key=True)
    estudio_id: Mapped[int] = mapped_column(
        ForeignKey("estudio_solicitado.id"), primary_key=True
    )


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


class AuditoriaAccion(Base):
    __tablename__ = "auditoria_accion"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    entidad_afectada: Mapped[str] = mapped_column(Text, nullable=False)
    referencia_registro: Mapped[str | None] = mapped_column(Text, nullable=True)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


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
