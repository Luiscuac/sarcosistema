from app.application.use_cases.listar_campos_editables import ListarCamposEditables
from app.application.use_cases.listar_ventanas import ListarVentanas
from app.application.use_cases.rellenar_campos import RellenarCampos
from app.application.use_cases.transportar_consulta_demo import TransportarConsultaDemo
from app.container import escritorio


def proveer_listar_ventanas() -> ListarVentanas:
    return ListarVentanas(escritorio)


def proveer_listar_campos() -> ListarCamposEditables:
    return ListarCamposEditables(escritorio)


def proveer_rellenar_campos() -> RellenarCampos:
    return RellenarCampos(escritorio)


def proveer_transportar_consulta_demo() -> TransportarConsultaDemo:
    return TransportarConsultaDemo(escritorio)
