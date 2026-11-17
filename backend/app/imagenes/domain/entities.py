"""Entidades del modulo de examenes complementarios de imagen."""
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class SolicitudEcografia:
    """Pedido del medico: genera solicitud y estudio pendiente para el personal de imágenes."""

    paciente_id: int
    tipo_estudio_ids: tuple[int, ...]
    medico_solicitante_nombre: str
    referencia: str
    clave_idempotencia: str
    prioridad: str = 'sin_prioridad'


@dataclass(frozen=True, slots=True)
class EstudioImagenPendiente:
    """Estudio de imagen en bandeja del personal de imágenes."""

    estudio_id: int
    referencia_estudio: str
    referencia_solicitud: str
    paciente_id: int
    paciente_nombre: str
    tipo_estudio_nombre: str
    prioridad: str
    estado: str
    fecha_solicitud: datetime
    cantidad_archivos: int = 0


@dataclass(frozen=True, slots=True)
class ArchivoImagen:
    """Metadatos de un archivo ya guardado (el binario vive fuera de la BD)."""

    id: int
    nombre_original: str
    mime_type: str
    tamano_bytes: int
    hash_sha256: str
    fecha_carga: datetime
    url_archivo: str


@dataclass(frozen=True, slots=True)
class InformeImagen:
    """Version del informe de un estudio; solo la publicada se muestra al medico."""

    id: int
    estudio_id: int
    numero_version: int
    descripcion_texto: str | None
    estado: str
    motivo_rectificacion: str | None
    fecha_hora_publicacion: datetime | None
    archivos: tuple[ArchivoImagen, ...] = ()
    datos_ecografia: dict | None = None


@dataclass(frozen=True, slots=True)
class EstudioImagenDetalle:
    """Vista de trabajo del personal de imágenes: estudio + ultima version del informe."""

    estudio_id: int
    referencia_estudio: str
    referencia_solicitud: str
    paciente_nombre: str
    tipo_estudio_nombre: str
    estado: str
    fecha_solicitud: datetime
    informe: InformeImagen | None
    tipo_estudio_codigo: str = ''
    codigo_paciente: str = ''
    historia_clinica: str | None = None
    fecha_nacimiento: date | None = None
    medico_solicitante: str | None = None


@dataclass(frozen=True, slots=True)
class EstudioImagenPublicado:
    """Resumen que ve el medico en el historial del paciente."""

    estudio_id: int
    referencia_estudio: str
    tipo_estudio_nombre: str
    fecha_solicitud: datetime
    fecha_publicacion: datetime | None
    descripcion_texto: str | None
    archivos: tuple[ArchivoImagen, ...] = ()
    datos_ecografia: dict | None = None
