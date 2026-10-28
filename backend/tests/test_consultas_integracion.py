"""Flujo completo contra PostgreSQL; todas las filas ficticias se revierten."""
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import engine, get_db
from app.main import app


@pytest.mark.asyncio
async def test_flujo_postgresql_login_busqueda_consulta_historial_reintento(client):
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        async with AsyncSession(bind=conexion, expire_on_commit=False) as sesion:
            async def db_de_prueba():
                yield sesion

            app.dependency_overrides[get_db] = db_de_prueba
            try:
                sufijo = uuid4().hex[:12]
                trabajador = (await sesion.execute(text('''
                    INSERT INTO public.trabajador (identificador, nombre_completo, estado, fecha_inicio)
                    VALUES (:codigo, 'Médico ficticio', 'activo', :fecha) RETURNING id
                '''), {'codigo': f'T-{sufijo}', 'fecha': date(2026, 1, 1)})).scalar_one()
                rol = (await sesion.execute(text("SELECT id FROM public.rol WHERE codigo = 'medico'"))).scalar_one()
                usuario = (await sesion.execute(text('''
                    INSERT INTO public.usuario (identificador_acceso, contrasena_hash, rol_id, trabajador_id, estado)
                    VALUES (:nombre, :hash, :rol, :trabajador, 'activo') RETURNING id
                '''), {'nombre': f'doc_{sufijo}', 'hash': Argon2PasswordHasher().hashear('clave-ficticia'),
                       'rol': rol, 'trabajador': trabajador})).scalar_one()
                medico = (await sesion.execute(text('''
                    INSERT INTO public.medico (trabajador_id, matricula_profesional)
                    VALUES (:trabajador, :matricula) RETURNING id
                '''), {'trabajador': trabajador, 'matricula': f'M-{sufijo}'})).scalar_one()
                especialidad = (await sesion.execute(text('''
                    INSERT INTO public.especialidad (codigo, nombre) VALUES (:codigo, 'Especialidad ficticia') RETURNING id
                '''), {'codigo': f'ESP_{sufijo}'})).scalar_one()
                await sesion.execute(text('''
                    INSERT INTO public.medico_especialidad (medico_id, especialidad_id, fecha_inicio, principal, vigente)
                    VALUES (:medico, :especialidad, :fecha, true, true)
                '''), {'medico': medico, 'especialidad': especialidad, 'fecha': date(2026, 1, 1)})
                paciente = (await sesion.execute(text('''
                    INSERT INTO public.paciente (codigo_paciente, nombre_completo, fecha_nacimiento, sexo,
                        sin_documento, estado) VALUES (:codigo, 'Paciente Ficticio Integración', :fecha,
                        'F', true, 'activo') RETURNING id
                '''), {'codigo': f'PAC-{sufijo}', 'fecha': date(1990, 1, 1)})).scalar_one()

                login = await client.post('/accesos/login', json={
                    'identificador_acceso': f'doc_{sufijo}', 'password': 'clave-ficticia',
                })
                assert login.status_code == 200, login.text
                headers = {'Authorization': f"Bearer {login.json()['access_token']}"}
                busqueda = await client.get('/consultas/pacientes', params={'buscar': 'Ficticio Integración'}, headers=headers)
                assert busqueda.status_code == 200, busqueda.text
                assert busqueda.json()['total'] >= 1
                assert any(p['id'] == paciente for p in busqueda.json()['items'])

                entrada = {'paciente_id': paciente, 'clave_idempotencia': str(uuid4()),
                           'motivo_consulta': 'Control ficticio', 'diagnostico_principal': 'Evaluación ficticia',
                           'peso_kg': 70, 'talla_cm': 175, 'tratamiento': 'Indicaciones ficticias'}
                creada = await client.post('/consultas', json=entrada, headers=headers)
                assert creada.status_code == 201, creada.text
                consulta = creada.json()
                assert consulta['medico_id'] == medico
                assert consulta['diagnostico_principal'] == 'Evaluación ficticia'
                repetida = await client.post('/consultas', json=entrada, headers=headers)
                assert repetida.status_code == 200, repetida.text
                assert repetida.json()['id'] == consulta['id']
                conflicto = await client.post('/consultas', json={**entrada, 'motivo_consulta': 'Otro'}, headers=headers)
                assert conflicto.status_code == 409
                conflicto_paciente = await client.post('/consultas', json={**entrada, 'paciente_id': 99999999}, headers=headers)
                assert conflicto_paciente.status_code == 409
                historia = await client.get(f'/consultas/pacientes/{paciente}/historial', headers=headers)
                assert historia.status_code == 200, historia.text
                assert historia.json()['total'] == 1
                await sesion.execute(text("UPDATE public.paciente SET estado = 'inactivo' WHERE id = :id"), {'id': paciente})
                detalle = await client.get(f"/consultas/{consulta['id']}", headers=headers)
                assert detalle.json()['tratamiento'] == 'Indicaciones ficticias'
                assert detalle.json()['paciente']['estado'] == 'inactivo'
                assert (await client.get(f'/consultas/pacientes/{paciente}', headers=headers)).status_code == 404
                auditorias = (await sesion.execute(text('''
                    SELECT count(*) FROM public.auditoria_accion
                    WHERE usuario_id = :usuario AND referencia_registro = :id
                '''), {'usuario': usuario, 'id': str(consulta['id'])})).scalar_one()
                assert auditorias == 1
                rol_lab = (await sesion.execute(text("SELECT id FROM public.rol WHERE codigo='laboratorio'"))).scalar_one()
                await sesion.execute(text('UPDATE public.usuario SET rol_id=:rol WHERE id=:id'), {'rol': rol_lab, 'id': usuario})
                assert (await client.get(f"/consultas/{consulta['id']}", headers=headers)).status_code == 403
            finally:
                app.dependency_overrides.clear()
                await transaccion.rollback()
