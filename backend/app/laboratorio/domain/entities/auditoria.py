from enum import StrEnum


class AccionAuditoria(StrEnum):
    """Acciones permitidas por el dominio de auditoría del esquema."""

    CREAR = "crear"
    MODIFICAR = "modificar"
    PUBLICAR = "publicar"
