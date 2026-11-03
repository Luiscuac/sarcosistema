from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.application.use_cases.listar_campos_editables import ListarCamposEditables
from app.application.use_cases.listar_ventanas import ListarVentanas
from app.application.use_cases.rellenar_campos import RellenarCampos
from app.application.use_cases.transportar_consulta_demo import TransportarConsultaDemo
from app.domain.entities import CampoDestino, ConsultaParaDemo
from app.presentation.dependencies import (
    proveer_listar_campos,
    proveer_listar_ventanas,
    proveer_rellenar_campos,
    proveer_transportar_consulta_demo,
)
from app.presentation.schemas.requests import (
    SolicitudRellenoRequest,
    SolicitudTransporteDemoRequest,
)
from app.presentation.schemas.responses import CampoEditableResponse, VentanaResponse


router = APIRouter()


@router.get("/health")
def health():
    return {"estado": "disponible", "agente": "SarcoSistema Windows UIA"}


@router.get("/v1/ventanas", response_model=list[VentanaResponse])
def obtener_ventanas(caso_uso: ListarVentanas = Depends(proveer_listar_ventanas)):
    return [asdict(ventana) for ventana in caso_uso.ejecutar()]


@router.get(
    "/v1/ventanas/{handle}/campos",
    response_model=list[CampoEditableResponse],
)
def obtener_campos_editables(
    handle: int,
    caso_uso: ListarCamposEditables = Depends(proveer_listar_campos),
):
    return [
        asdict(campo)
        for campo in caso_uso.ejecutar(handle)
    ]


@router.post("/v1/ventanas/{handle}/rellenar")
def rellenar_ventana(
    handle: int,
    solicitud: SolicitudRellenoRequest,
    caso_uso: RellenarCampos = Depends(proveer_rellenar_campos),
):
    campos = [CampoDestino(**campo.model_dump()) for campo in solicitud.campos]
    return caso_uso.ejecutar(handle, campos)


@router.post("/v1/demo/transportar-consulta")
def transportar_consulta(
    solicitud: SolicitudTransporteDemoRequest,
    caso_uso: TransportarConsultaDemo = Depends(proveer_transportar_consulta_demo),
):
    consulta = ConsultaParaDemo(**solicitud.model_dump())
    return caso_uso.ejecutar(consulta)
