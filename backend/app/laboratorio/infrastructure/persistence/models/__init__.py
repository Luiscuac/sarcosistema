"""Modelos ORM del laboratorio, agrupados por flujo de datos."""

from app.laboratorio.infrastructure.persistence.models.catalogo import (
    Servicio,
    TipoEstudio,
)

from app.laboratorio.infrastructure.persistence.models.solicitudes import (
    Solicitud,
    EstudioSolicitado,
    EstudioEstadoHistorial,
)

from app.laboratorio.infrastructure.persistence.models.muestras import (
    Muestra,
    MuestraEstudio,
)

from app.laboratorio.infrastructure.persistence.models.plantillas import (
    PlantillaExamen,
    PlantillaExamenVersion,
    SeccionPlantilla,
    ParametroPlantilla,
    OpcionParametro,
)

from app.laboratorio.infrastructure.persistence.models.resultados import (
    ResultadoLaboratorio,
    VersionResultado,
    DetalleValorResultado,
)

from app.laboratorio.infrastructure.persistence.models.auditoria import (
    AuditoriaAccion,
)

__all__ = [
    "Servicio",
    "TipoEstudio",
    "Solicitud",
    "EstudioSolicitado",
    "EstudioEstadoHistorial",
    "Muestra",
    "MuestraEstudio",
    "PlantillaExamen",
    "PlantillaExamenVersion",
    "SeccionPlantilla",
    "ParametroPlantilla",
    "OpcionParametro",
    "ResultadoLaboratorio",
    "VersionResultado",
    "DetalleValorResultado",
    "AuditoriaAccion",
]
