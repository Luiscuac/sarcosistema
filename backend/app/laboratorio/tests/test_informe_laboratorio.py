"""El informe final reúne exclusivamente resultados publicados e informados."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.laboratorio.application.use_cases.service import LaboratorioService


def solicitud(estado="publicado"):
    return {
        "referencia": "SOL-9", "paciente_nombre": "Paciente ficticio",
        "paciente_documento": "12345678", "fecha_solicitud": datetime(2026, 11, 2, tzinfo=timezone.utc),
        "referencia_papel_formulario": "0391521", "procedencia": "este_centro",
        "establecimiento_solicitante_nombre": None, "medico_solicitante_nombre": "Dra. Ficticia",
        "fecha_registro": datetime(2026, 11, 2, tzinfo=timezone.utc),
        "estudios": [{
            "estudio_id": 5, "estado": estado, "categoria_laboratorio": "bioquimica",
            "tipo_estudio_nombre": "Química sanguínea", "referencia_estudio": "EST-5",
            "incidencias": [],
        }],
    }


@pytest.mark.asyncio
async def test_informe_excluye_parametros_vacios_y_conserva_referencias():
    class Repositorio:
        async def obtener_solicitud(self, solicitud_id):
            assert solicitud_id == 9
            return solicitud()

        async def obtener_resultado(self, estudio_id):
            assert estudio_id == 5
            return SimpleNamespace(
                estado_resultado="publicado", tipo_estudio_nombre="Química sanguínea",
                referencia_estudio="EST-5", observaciones="  Sin novedades  ",
                responsable_publicacion="Ana Pérez",
                parametros=(
                    SimpleNamespace(codigo="glicemia", nombre="Glicemia", seccion="Bioquímica", valor="90", unidad="mg/dl", rango_referencia="70-115"),
                    SimpleNamespace(codigo="creatinina", nombre="Creatinina", seccion="Bioquímica", valor="  ", unidad="mg/dl", rango_referencia="0.6-1.3"),
                    SimpleNamespace(codigo="urea", nombre="Urea", seccion="Bioquímica", valor=None, unidad="mg/dl", rango_referencia="10-50"),
                    SimpleNamespace(codigo="unidad_reportada", nombre="Unidad (si aplica)", seccion="Bioquímica", valor="g", unidad=None, rango_referencia=None),
                ),
            )

    informe = await LaboratorioService(Repositorio()).obtener_informe(9)
    assert informe["referencia"] == "SOL-9"
    assert informe["resultados"][0]["parametros"] == [{
        "nombre": "Glicemia", "seccion": "Bioquímica", "valor": "90",
        "unidad": "mg/dl", "rango_referencia": "70-115",
    }]
    assert informe["resultados"][0]["observaciones"] == "Sin novedades"
    assert informe["estudios_no_realizados"] == []


@pytest.mark.asyncio
async def test_informe_incluye_estudio_no_realizado_sin_buscar_un_resultado():
    fecha = datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc)

    class Repositorio:
        async def obtener_solicitud(self, solicitud_id):
            pedido = solicitud("no_realizado")
            pedido["estudios"][0]["incidencias"] = [{
                "motivo": "muestra_no_entregada",
                "descripcion": "El paciente no entregó la muestra de orina",
                "responsable": "Ana Pérez",
                "fecha_hora": fecha,
            }]
            return pedido

        async def obtener_resultado(self, estudio_id):
            pytest.fail("Un estudio no realizado no debe tener resultado de laboratorio")

    informe = await LaboratorioService(Repositorio()).obtener_informe(9)
    assert informe["resultados"] == []
    assert informe["estudios_no_realizados"] == [{
        "nombre": "Química sanguínea",
        "categoria": "bioquimica",
        "referencia": "EST-5",
        "motivo": "muestra_no_entregada",
        "descripcion": "El paciente no entregó la muestra de orina",
        "responsable": "Ana Pérez",
        "fecha_hora": fecha,
    }]


@pytest.mark.asyncio
@pytest.mark.parametrize("estado", ["pendiente_muestra", "resultado_en_preparacion"])
async def test_informe_no_consulta_resultados_si_la_solicitud_esta_incompleta(estado):
    class Repositorio:
        async def obtener_solicitud(self, solicitud_id):
            pedido = solicitud()
            pedido["estudios"].append({
                "estudio_id": 6, "estado": estado, "categoria_laboratorio": "hematologia",
                "tipo_estudio_nombre": "Hemograma", "referencia_estudio": "EST-6", "incidencias": [],
            })
            return pedido

        async def obtener_resultado(self, estudio_id):
            pytest.fail("Un estudio pendiente no debe leerse para el informe")

    with pytest.raises(ValueError, match="todos los estudios estén publicados o cerrados"):
        await LaboratorioService(Repositorio()).obtener_informe(9)


@pytest.mark.asyncio
async def test_informe_rechaza_borrador_aunque_el_estado_del_estudio_sea_publicado():
    class Repositorio:
        async def obtener_solicitud(self, solicitud_id):
            return solicitud()

        async def obtener_resultado(self, estudio_id):
            return SimpleNamespace(estado_resultado="borrador")

    with pytest.raises(ValueError, match="todos los resultados estén publicados"):
        await LaboratorioService(Repositorio()).obtener_informe(9)
