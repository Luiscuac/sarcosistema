"""Entidades de dominio del laboratorio, agrupadas por flujo."""

from app.laboratorio.domain.entities.catalogo import EstudioCatalogo, EstudioPendiente
from app.laboratorio.domain.entities.muestras import MuestraSolicitudNueva, TomaMuestraNueva
from app.laboratorio.domain.entities.pacientes import PacienteNuevo, PacienteResumen
from app.laboratorio.domain.entities.resultados import (
    BorradorResultado,
    ParametroResultado,
    ResultadoEstudio,
    ValorResultadoEntrada,
)
from app.laboratorio.domain.entities.solicitudes import (
    EstudioSolicitadoResumen,
    SolicitudCreada,
    SolicitudNueva,
)
from app.laboratorio.domain.entities.auditoria import AccionAuditoria

__all__ = [
    "AccionAuditoria", "BorradorResultado", "EstudioCatalogo", "EstudioPendiente",
    "EstudioSolicitadoResumen", "MuestraSolicitudNueva", "PacienteNuevo",
    "PacienteResumen", "ParametroResultado", "ResultadoEstudio", "SolicitudCreada",
    "SolicitudNueva", "TomaMuestraNueva", "ValorResultadoEntrada",
]
