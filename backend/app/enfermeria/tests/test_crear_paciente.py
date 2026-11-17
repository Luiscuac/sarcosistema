from datetime import date

import pytest

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.enfermeria.presentation.router import get_paciente_service
from app.laboratorio.domain.entities import PacienteResumen
from app.main import app


@pytest.fixture
def paciente_registro(monkeypatch):
    class Servicio:
        recibido = None

        async def crear_paciente(self, paciente, usuario_id):
            self.recibido = paciente, usuario_id
            return PacienteResumen(
                41, 'PAC-41', paciente.nombre_completo, paciente.numero_documento,
                paciente.fecha_nacimiento, paciente.sexo, paciente.historia_clinica,
                paciente.codigo_externo, paciente.telefono,
            )

    servicio = Servicio()
    usuario = Usuario(
        id=7,
        identificador_acceso='admision_prueba',
        rol='enfermeria',
        activo=True,
        contrasena_hash='hash',
    )
    monkeypatch.setitem(app.dependency_overrides, usuario_actual, lambda: usuario)
    monkeypatch.setitem(app.dependency_overrides, get_paciente_service, lambda: servicio)
    return servicio, usuario


@pytest.mark.asyncio
async def test_enfermeria_crea_paciente_y_devuelve_ficha_para_continuar_admision(client, paciente_registro):
    servicio, usuario = paciente_registro
    response = await client.post('/enfermeria/pacientes', json={
        'nombre_completo': 'Paciente ficticio',
        'fecha_nacimiento': '1990-01-02',
        'sexo': 'F',
        'tipo_documento': 'CI',
        'numero_documento': '12345678',
        'sin_documento': False,
    })

    assert response.status_code == 201
    assert response.json()['id'] == 41
    assert response.json()['codigo_paciente'] == 'PAC-41'
    assert servicio.recibido[1] == usuario.id
    assert servicio.recibido[0].fecha_nacimiento == date(1990, 1, 2)


@pytest.mark.asyncio
async def test_crear_paciente_en_admisiones_requiere_rol_enfermeria(client, paciente_registro):
    _, usuario = paciente_registro
    usuario.rol = 'laboratorio'

    response = await client.post('/enfermeria/pacientes', json={
        'nombre_completo': 'Paciente ficticio',
        'fecha_nacimiento': '1990-01-02',
        'sexo': 'F',
        'tipo_documento': 'CI',
        'numero_documento': '12345678',
        'sin_documento': False,
    })

    assert response.status_code == 403
