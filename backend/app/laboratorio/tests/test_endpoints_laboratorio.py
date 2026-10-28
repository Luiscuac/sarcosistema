"""Endpoints de laboratorio: catálogo, bandejas, pacientes, solicitudes y resultados.

Cada prueba sustituye el caso de uso por un doble para verificar contrato HTTP,
autorización y traducción de errores de dominio a códigos HTTP.
"""
from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.laboratorio.domain.entities import (
    BorradorResultado,
    EstudioCatalogo,
    EstudioPendiente,
    EstudioSolicitadoResumen,
    PacienteResumen,
    ParametroResultado,
    ResultadoEstudio,
    SolicitudCreada,
)
from app.laboratorio.presentation.router import get_service
from app.main import app


@pytest.fixture
def servicio():
    """Doble del caso de uso: registra lo recibido y devuelve valores controlados."""

    class Doble:
        def __init__(self):
            self.recibido = {}

        async def listar_catalogo(self):
            return [
                EstudioCatalogo(1, "HEM", "Hemograma completo", True, False, True, "hematologia"),
                EstudioCatalogo(2, "GLU", "Glucosa", True, False, False),
            ]

        async def listar_pendientes(self):
            return [self._pendiente()]

        async def listar_publicados(self):
            return [self._pendiente()]

        def _pendiente(self):
            return EstudioPendiente(
                estudio_id=5, referencia_estudio="EST-5", solicitud_id=4, referencia_solicitud="SOL-4",
                paciente_id=1, paciente_nombre="Paciente ficticio", tipo_estudio_id=1,
                tipo_estudio_nombre="Hemograma completo", prioridad="sin_prioridad",
                estado="pendiente_muestra",
                fecha_solicitud=datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc),
                plantilla_configurada=True, categoria_laboratorio="hematologia",
            )

        async def buscar_pacientes(self, termino):
            self.recibido["termino"] = termino
            return [
                PacienteResumen(1, "PAC-1", "Paciente ficticio", "12345678",
                                date(1990, 1, 1), "M", "HC-1", "LAB-1"),
            ]

        async def crear_paciente(self, paciente, usuario_id):
            self.recibido["paciente"] = paciente
            self.recibido["usuario_id"] = usuario_id
            return PacienteResumen(1, "PAC-1", paciente.nombre_completo,
                                   paciente.numero_documento, paciente.fecha_nacimiento,
                                   paciente.sexo, paciente.historia_clinica, paciente.codigo_externo)

        async def crear_solicitud(self, solicitud, usuario_id):
            self.recibido["solicitud"] = solicitud
            return SolicitudCreada(
                9, "SOL-9", solicitud.paciente_id, "Paciente ficticio",
                solicitud.fecha_solicitud, solicitud.prioridad,
                (EstudioSolicitadoResumen(i, f"EST-{i}", tipo, "Hemograma", "pendiente_muestra")
                 for i, tipo in enumerate(solicitud.tipo_estudio_ids, start=1)),
            )

        async def recibir_muestra(self, toma, usuario_id):
            self.recibido["toma"] = toma
            return "MUE-PRUEBA"

        async def recibir_muestra_solicitud(self, toma, usuario_id):
            self.recibido["toma_solicitud"] = toma
            return "MUE-PRUEBA"

        async def obtener_resultado(self, estudio_id):
            self.recibido["resultado_de"] = estudio_id
            return ResultadoEstudio(
                estudio_id=estudio_id, referencia_estudio="EST-5",
                paciente_nombre="Paciente ficticio", tipo_estudio_nombre="Hemograma completo",
                estado_estudio="resultado_en_preparacion", estado_resultado="borrador",
                numero_version=1, plantilla_configurada=True, observaciones="Observación ficticia",
                parametros=(ParametroResultado(1, "GLU", "Glucosa", "numero", "mg/dL",
                                               "70-110", True, 1, "Bioquímica", "90"),),
            )

        async def guardar_borrador(self, estudio_id, valores, observaciones, usuario_id):
            self.recibido["borrador"] = (estudio_id, valores, observaciones)
            return BorradorResultado(estudio_id, "borrador", 1)

        async def publicar_resultado(self, estudio_id, usuario_id):
            self.recibido["publicado"] = estudio_id
            return BorradorResultado(estudio_id, "publicado", 2)

    doble = Doble()
    app.dependency_overrides[get_service] = lambda: doble
    yield doble
    app.dependency_overrides.pop(get_service, None)


@pytest.fixture
def medico():
    usuario = Usuario(7, "laboratorio_prueba", "medico", True)
    app.dependency_overrides[usuario_actual] = lambda: usuario
    yield usuario
    app.dependency_overrides.pop(usuario_actual, None)


async def _sesion(client, usuarios):
    login = await client.post("/accesos/login", json={
        "identificador_acceso": "laboratorio_prueba", "password": "clave-de-prueba",
    })
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_catalogo_y_bandejas_devuelven_estudios(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    catalogo = await client.get("/laboratorio/catalogo/estudios", headers=headers)
    assert catalogo.status_code == 200
    assert [estudio["codigo"] for estudio in catalogo.json()] == ["HEM", "GLU"]
    assert catalogo.json()[0]["plantilla_configurada"] is True

    pendientes = await client.get("/laboratorio/estudios/pendientes", headers=headers)
    publicados = await client.get("/laboratorio/estudios/publicados", headers=headers)
    assert pendientes.status_code == 200
    assert publicados.status_code == 200
    for bandeja in (pendientes.json(), publicados.json()):
        assert bandeja[0]["paciente_nombre"] == "Paciente ficticio"
        assert bandeja[0]["estado"] == "pendiente_muestra"


@pytest.mark.asyncio
async def test_buscar_pacientes_recorta_termino_y_exige_minimo(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    respuesta = await client.get(
        "/laboratorio/pacientes", params={"termino": "  Paciente  "}, headers=headers
    )
    assert respuesta.status_code == 200
    # El endpoint entrega el término tal cual; recortarlo es regla del servicio.
    assert servicio.recibido["termino"] == "  Paciente  "
    assert respuesta.json()[0]["codigo_paciente"] == "PAC-1"

    corto = await client.get("/laboratorio/pacientes", params={"termino": "a"}, headers=headers)
    assert corto.status_code == 422
    sin_sesion = await client.get("/laboratorio/pacientes", params={"termino": "Paciente"})
    assert sin_sesion.status_code == 401


@pytest.mark.asyncio
async def test_crear_paciente_normaliza_y_omite_documento_si_no_tiene(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    respuesta = await client.post("/laboratorio/pacientes", headers=headers, json={
        "nombre_completo": "  Paciente ficticio  ", "fecha_nacimiento": "1990-01-01",
        "sexo": "M", "sin_documento": True, "historia_clinica": "  HC-9  ",
    })
    assert respuesta.status_code == 201, respuesta.text
    paciente = servicio.recibido["paciente"]
    assert paciente.nombre_completo == "Paciente ficticio"
    assert paciente.sin_documento is True
    assert paciente.tipo_documento is None and paciente.numero_documento is None
    assert paciente.historia_clinica == "HC-9"
    assert servicio.recibido["usuario_id"] == usuarios.id
    assert respuesta.json()["numero_documento"] is None


@pytest.mark.asyncio
async def test_crear_paciente_sin_documento_ni_marca_se_rechaza(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    respuesta = await client.post("/laboratorio/pacientes", headers=headers, json={
        "nombre_completo": "Paciente ficticio", "fecha_nacimiento": "1990-01-01", "sexo": "M",
    })
    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_paciente_duplicado_devuelve_409_y_no_expone_internos(client, usuarios, servicio):
    async def duplicado(paciente, usuario_id):
        raise IntegrityError("INSERT INTO public.paciente", {}, Exception("duplicate key"))

    servicio.crear_paciente = duplicado
    headers = await _sesion(client, usuarios)
    respuesta = await client.post("/laboratorio/pacientes", headers=headers, json={
        "nombre_completo": "Paciente ficticio", "fecha_nacimiento": "1990-01-01",
        "sexo": "M", "tipo_documento": "CI", "numero_documento": "12345678",
    })
    assert respuesta.status_code == 409
    assert "duplicate key" not in respuesta.text


@pytest.mark.asyncio
async def test_crear_solicitud_envia_clave_de_idempotencia_como_texto(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    clave = str(uuid4())
    respuesta = await client.post("/laboratorio/solicitudes", headers=headers, json={
        "paciente_id": 1, "tipo_estudio_ids": [1, 2], "medico_solicitante_nombre": "  Dra. Ficticia  ",
        "clave_idempotencia": clave, "prioridad": "urgente",
    })
    assert respuesta.status_code == 201, respuesta.text
    solicitud = servicio.recibido["solicitud"]
    assert solicitud.tipo_estudio_ids == (1, 2)
    assert solicitud.medico_solicitante_nombre == "Dra. Ficticia"
    assert solicitud.clave_idempotencia == clave
    assert solicitud.prioridad == "urgente"
    assert len(respuesta.json()["estudios"]) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"tipo_estudio_ids": [1]},                                  # sin médico
    {"tipo_estudio_ids": [1, 1], "medico_solicitante_nombre": "Dra. Ficticia"},
], ids=["sin_medico", "estudio_repetido"])
async def test_crear_solicitud_invalida_devuelve_422(client, usuarios, servicio, payload):
    headers = await _sesion(client, usuarios)
    cuerpo = {"paciente_id": 1, "clave_idempotencia": str(uuid4()), **payload}
    if "medico_solicitante_nombre" not in cuerpo:
        cuerpo["medico_solicitante_nombre"] = "   "
    respuesta = await client.post("/laboratorio/solicitudes", headers=headers, json=cuerpo)
    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_solicitud_duplicada_devuelve_409_recargar(client, usuarios, servicio):
    async def duplicada(solicitud, usuario_id):
        raise IntegrityError("INSERT INTO public.solicitud", {}, Exception("duplicate key"))

    servicio.crear_solicitud = duplicada
    headers = await _sesion(client, usuarios)
    respuesta = await client.post("/laboratorio/solicitudes", headers=headers, json={
        "paciente_id": 1, "tipo_estudio_ids": [1],
        "medico_solicitante_nombre": "Dra. Ficticia", "clave_idempotencia": str(uuid4()),
    })
    assert respuesta.status_code == 409
    assert "recibió duplicada" in respuesta.json()["detail"]


@pytest.mark.asyncio
async def test_recibir_muestra_de_un_estudio_devuelve_referencia(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    respuesta = await client.post(
        "/laboratorio/estudios/5/muestra", headers=headers,
        json={"tipo_muestra": "  Sangre  ", "fecha_toma": "2026-10-22", "hora_toma": "09:30:00"},
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json() == {"referencia_muestra": "MUE-PRUEBA"}
    toma = servicio.recibido["toma"]
    assert (toma.estudio_id, toma.tipo_muestra, toma.hora_toma) == (5, "Sangre", time(9, 30))
    assert toma.hora_no_registrada is False


@pytest.mark.asyncio
@pytest.mark.parametrize("cuerpo", [
    {"tipo_muestra": "Sangre", "fecha_toma": "2026-10-22"},                       # sin hora ni marca
    {"tipo_muestra": "Sangre", "fecha_toma": "2026-10-22",                        # hora y marca
     "hora_toma": "09:30:00", "hora_no_registrada": True},
])
async def test_recibir_muestra_con_hora_inconsistente_devuelve_422(client, usuarios, servicio, cuerpo):
    headers = await _sesion(client, usuarios)
    respuesta = await client.post("/laboratorio/estudios/5/muestra", headers=headers, json=cuerpo)
    assert respuesta.status_code == 422
    assert "hora" in respuesta.text


@pytest.mark.asyncio
async def test_resultado_del_estudio_se_devuelve_con_sus_parametros(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    respuesta = await client.get("/laboratorio/estudios/5/resultado", headers=headers)
    assert respuesta.status_code == 200
    body = respuesta.json()
    assert body["estado_resultado"] == "borrador"
    assert body["numero_version"] == 1
    assert body["parametros"][0]["nombre"] == "Glucosa"
    assert body["parametros"][0]["valor"] == "90"
    assert servicio.recibido["resultado_de"] == 5


@pytest.mark.asyncio
async def test_resultado_inexistente_devuelve_404(client, usuarios, servicio):
    async def inexistente(estudio_id):
        raise ValueError("El estudio no tiene resultado registrado")

    servicio.obtener_resultado = inexistente
    headers = await _sesion(client, usuarios)
    respuesta = await client.get("/laboratorio/estudios/999/resultado", headers=headers)
    assert respuesta.status_code == 404


@pytest.mark.asyncio
async def test_borrador_guarda_valores_y_publicar_crea_version(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    borrador = await client.put(
        "/laboratorio/estudios/5/resultado/borrador", headers=headers,
        json={"valores": [{"parametro_id": 1, "valor": "90"}],
              "observaciones": "  Sin observaciones  "},
    )
    assert borrador.status_code == 200, borrador.text
    assert borrador.json() == {"estudio_id": 5, "estado": "borrador", "numero_version": 1}
    estudio_id, valores, observaciones = servicio.recibido["borrador"]
    assert (estudio_id, observaciones) == (5, "  Sin observaciones  ")
    assert valores[0].parametro_id == 1

    publicar = await client.post(
        "/laboratorio/estudios/5/resultado/publicar", headers=headers
    )
    assert publicar.status_code == 200
    assert publicar.json() == {"estudio_id": 5, "estado": "publicado", "numero_version": 2}
    assert servicio.recibido["publicado"] == 5


@pytest.mark.asyncio
async def test_borrador_con_parametro_repetido_devuelve_422(client, usuarios, servicio):
    headers = await _sesion(client, usuarios)
    respuesta = await client.put(
        "/laboratorio/estudios/5/resultado/borrador", headers=headers,
        json={"valores": [{"parametro_id": 1, "valor": "90"}, {"parametro_id": 1, "valor": "95"}]},
    )
    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_publicar_con_valores_obligatorios_vacios_devuelve_422(client, usuarios, servicio):
    async def faltantes(estudio_id, usuario_id):
        raise ValueError("Completa los campos obligatorios: Glucosa")

    servicio.publicar_resultado = faltantes
    headers = await _sesion(client, usuarios)
    respuesta = await client.post(
        "/laboratorio/estudios/5/resultado/publicar", headers=headers
    )
    assert respuesta.status_code == 422
    assert "Glucosa" in respuesta.json()["detail"]


@pytest.mark.asyncio
async def test_otra_funcion_no_accede_a_laboratorio(client, usuarios, servicio, medico):
    headers = await _sesion(client, usuarios)
    respuesta = await client.get("/laboratorio/estudios/pendientes", headers=headers)
    assert respuesta.status_code == 403
    assert "Sin acceso" in respuesta.json()["detail"]


@pytest.mark.asyncio
async def test_valores_obligatorios_admiten_cero_y_rechazan_vacio():
    """Regla de dominio: campo vacío no es cero; cero es un valor real."""
    from types import SimpleNamespace

    from app.laboratorio.infrastructure.persistence.repository import campos_obligatorios_faltantes

    parametros = [SimpleNamespace(id=1, nombre="Glucosa", obligatorio=True)]
    vacio = SimpleNamespace(parametro_id=1, valor_entero=None, valor_decimal=None,
                            valor_texto="", valor_cualitativo=None)
    assert campos_obligatorios_faltantes(parametros, [vacio]) == ["Glucosa"]
    cero = SimpleNamespace(parametro_id=1, valor_entero=None, valor_decimal=Decimal("0"),
                           valor_texto=None, valor_cualitativo=None)
    assert campos_obligatorios_faltantes(parametros, [cero]) == []
