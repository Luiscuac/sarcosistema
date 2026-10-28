"""Los registros de demostración deben ser inequívocos y no pisar cuentas existentes."""
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from scripts import preparar_medico_demo as demo


engine = create_async_engine(settings.database_url, poolclass=NullPool)


@pytest.fixture
def identificadores(monkeypatch):
    sufijo = uuid4().hex[:12]
    for nombre in ('USUARIO_DEMO', 'TRABAJADOR_DEMO', 'ESPECIALIDAD_DEMO', 'PACIENTE_DEMO'):
        monkeypatch.setattr(demo, nombre, f'{getattr(demo, nombre)}_{sufijo}')


@pytest.mark.asyncio
async def test_prepara_medico_y_paciente_ficticios_sin_tocar_otros_usuarios(identificadores):
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            async with AsyncSession(bind=conexion) as sesion:
                antes = (await sesion.execute(text('SELECT count(*) FROM public.usuario'))).scalar_one()
                resultado = await demo.preparar_medico_demo(sesion, 'hash-ficticio')
                assert resultado['usuario'] == demo.USUARIO_DEMO
                assert resultado['codigo_paciente'] == demo.PACIENTE_DEMO
                assert (await sesion.execute(text('SELECT count(*) FROM public.usuario'))).scalar_one() == antes + 1
                asignacion = (await sesion.execute(text('''
                    SELECT me.vigente, e.nombre FROM public.medico_especialidad me
                    JOIN public.especialidad e ON e.id = me.especialidad_id
                    JOIN public.medico m ON m.id = me.medico_id
                    JOIN public.trabajador t ON t.id = m.trabajador_id
                    WHERE t.identificador = :identificador
                '''), {'identificador': demo.TRABAJADOR_DEMO})).one()
                assert asignacion.vigente is True
                assert 'PRUEBA' in asignacion.nombre
        finally:
            await transaccion.rollback()


@pytest.mark.asyncio
async def test_no_reemplaza_cuenta_demo_existente(identificadores):
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            async with AsyncSession(bind=conexion) as sesion:
                await demo.preparar_medico_demo(sesion, 'primer-hash')
                with pytest.raises(ValueError, match='ya existe'):
                    await demo.preparar_medico_demo(sesion, 'otro-hash')
                cuenta = (await sesion.execute(text('''
                    SELECT contrasena_hash FROM public.usuario WHERE identificador_acceso = :nombre
                '''), {'nombre': demo.USUARIO_DEMO})).scalar_one()
                assert cuenta == 'primer-hash'
        finally:
            await transaccion.rollback()
