"""Esquemas HTTP del modulo de examenes complementarios de imagen."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.imagenes.domain.errors import SolicitudInvalida


class SolicitudEcografiaRequest(BaseModel):
    paciente_id: int = Field(gt=0)
    tipo_estudio_ids: list[int] = Field(min_length=1, max_length=30)
    medico_solicitante_nombre: str = Field(min_length=2, max_length=200)
    clave_idempotencia: str | None = Field(default=None, max_length=80)
    prioridad: Literal['urgente', 'sin_prioridad'] = 'sin_prioridad'

    def validar_estudios(self) -> None:
        if any(tipo_id <= 0 for tipo_id in self.tipo_estudio_ids):
            raise SolicitudInvalida('Cada estudio debe tener un identificador válido')
        if len(self.tipo_estudio_ids) != len(set(self.tipo_estudio_ids)):
            raise SolicitudInvalida('No repitas el mismo estudio en una solicitud')

    def modelo_solicitud(self):
        from app.imagenes.domain.entities import SolicitudEcografia

        return SolicitudEcografia(
            paciente_id=self.paciente_id,
            tipo_estudio_ids=tuple(dict.fromkeys(self.tipo_estudio_ids)),
            medico_solicitante_nombre=self.medico_solicitante_nombre.strip(),
            clave_idempotencia=self.clave_idempotencia or '',
            referencia='',
            prioridad=self.prioridad,
        )


class ArchivoImagenResponse(BaseModel):
    id: int
    nombre_original: str
    mime_type: str
    tamano_bytes: int
    hash_sha256: str
    fecha_carga: datetime

    model_config = ConfigDict(from_attributes=True)


class InformeImagenResponse(BaseModel):
    id: int
    estudio_id: int
    numero_version: int
    descripcion_texto: str | None
    estado: str
    fecha_hora_publicacion: datetime | None
    archivos: list[ArchivoImagenResponse]

    model_config = ConfigDict(from_attributes=True)


class EstudioPendienteResponse(BaseModel):
    estudio_id: int
    referencia_estudio: str
    referencia_solicitud: str
    paciente_id: int
    paciente_nombre: str
    tipo_estudio_nombre: str
    prioridad: str
    estado: str
    fecha_solicitud: datetime

    model_config = ConfigDict(from_attributes=True)


class EstudioDetalleResponse(BaseModel):
    estudio_id: int
    referencia_estudio: str
    referencia_solicitud: str
    paciente_nombre: str
    tipo_estudio_nombre: str
    estado: str
    fecha_solicitud: datetime
    informe: InformeImagenResponse | None


class InformeRequest(BaseModel):
    descripcion: str | None = Field(default=None, max_length=8000)


class ResultadoAccionResponse(BaseModel):
    estudio_id: int
    estado: str
    numero_version: int


class EstudioPublicadoResponse(BaseModel):
    estudio_id: int
    referencia_estudio: str
    tipo_estudio_nombre: str
    fecha_solicitud: datetime
    fecha_publicacion: datetime | None
    descripcion_texto: str | None
    archivos: list[ArchivoImagenResponse]

    model_config = ConfigDict(from_attributes=True)


class SolicitudEcografiaResponse(BaseModel):
    solicitud_id: int
    estudios: list[int]
