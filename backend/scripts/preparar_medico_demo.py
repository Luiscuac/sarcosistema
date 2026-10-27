"""Alta optativa y no destructiva de un médico y paciente SOLO DE PRUEBA.

Uso: desde backend, python -m scripts.preparar_medico_demo
Genera una clave aleatoria en un archivo local fuera del repositorio. No la
imprime, ni la guarda como texto en la base de datos ni en el código fuente.
"""
import asyncio
import os
from pathlib import Path
import secrets

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import SessionLocal
from app.config.settings import settings

USUARIO_DEMO = 'medico_demo'
TRABAJADOR_DEMO = 'T-DEMO-CONSULTA-001'
ESPECIALIDAD_DEMO = 'DEMO_CONSULTA_GENERAL'
PACIENTE_DEMO = 'PAC-DEMO-CONSULTA-001'


async def preparar_medico_demo(db, password_hash: str) -> dict[str, str]:
    """Solo insertar registros reservados; ante colisión abortar sin cambios."""
    revisiones = (await db.execute(text("SELECT to_regclass('public.alembic_version')"))).scalar_one()
    if revisiones is None:
        raise ValueError('Primero aplica las migraciones con alembic upgrade head.')
    version = (await db.execute(text('SELECT version_num FROM public.alembic_version'))).scalar_one_or_none()
    if version != '20261027_0007':
        raise ValueError('La base necesita la revisión 20261027_0007 antes de crear datos de prueba.')

    for tabla, columna, identificador in (
        ('usuario', 'identificador_acceso', USUARIO_DEMO),
        ('trabajador', 'identificador', TRABAJADOR_DEMO),
        ('especialidad', 'codigo', ESPECIALIDAD_DEMO),
        ('paciente', 'codigo_paciente', PACIENTE_DEMO),
    ):
        existe = (await db.execute(text(
            f'SELECT 1 FROM public.{tabla} WHERE {columna} = :identificador'
        ), {'identificador': identificador})).first()
        if existe:
            raise ValueError(f'El registro de prueba {identificador} ya existe; no se modificó nada.')

    rol = (await db.execute(text('''
        SELECT id FROM public.rol WHERE codigo = 'medico' AND activo = true
    '''))).scalar_one_or_none()
    if rol is None:
        raise ValueError('No existe el rol medico activo; no se creó ningún registro.')

    trabajador = (await db.execute(text('''
        INSERT INTO public.trabajador (identificador, nombre_completo, estado, fecha_inicio)
        VALUES (:identificador, 'Profesional ficticio de demostración', 'activo', CURRENT_DATE)
        RETURNING id
    '''), {'identificador': TRABAJADOR_DEMO})).scalar_one()
    await db.execute(text('''
        INSERT INTO public.usuario (identificador_acceso, contrasena_hash, rol_id, trabajador_id, estado)
        VALUES (:identificador, :hash, :rol, :trabajador, 'activo')
    '''), {'identificador': USUARIO_DEMO, 'hash': password_hash,
           'rol': rol, 'trabajador': trabajador})
    medico = (await db.execute(text('''
        INSERT INTO public.medico (trabajador_id, matricula_profesional, activo)
        VALUES (:trabajador, 'DEMO-SIN-VALIDEZ-001', true) RETURNING id
    '''), {'trabajador': trabajador})).scalar_one()
    especialidad = (await db.execute(text('''
        INSERT INTO public.especialidad (codigo, nombre, activo)
        VALUES (:codigo, 'Medicina general (SOLO PRUEBA)', true) RETURNING id
    '''), {'codigo': ESPECIALIDAD_DEMO})).scalar_one()
    await db.execute(text('''
        INSERT INTO public.medico_especialidad
            (medico_id, especialidad_id, fecha_inicio, principal, vigente)
        VALUES (:medico, :especialidad, CURRENT_DATE, true, true)
    '''), {'medico': medico, 'especialidad': especialidad})
    await db.execute(text('''
        INSERT INTO public.paciente
            (codigo_paciente, nombre_completo, fecha_nacimiento, sexo, sin_documento, estado)
        VALUES (:codigo, 'Paciente ficticio de consulta', DATE '1990-01-01',
                'F', true, 'activo')
    '''), {'codigo': PACIENTE_DEMO})
    return {'usuario': USUARIO_DEMO, 'codigo_paciente': PACIENTE_DEMO}


async def main() -> None:
    if make_url(settings.database_url).host not in ('localhost', '127.0.0.1'):
        raise SystemExit('Este preparador solo se permite contra PostgreSQL local.')
    clave = secrets.token_urlsafe(18)
    carpeta = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))) / 'Temp' / 'opencode'
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f'medico_demo_clave_{secrets.token_hex(6)}.txt'
    try:
        descriptor = os.open(destino, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as archivo:
            archivo.write(clave)
        async with SessionLocal.begin() as db:
            resultado = await preparar_medico_demo(db, Argon2PasswordHasher().hashear(clave))
    except BaseException:
        destino.unlink(missing_ok=True)
        raise
    print(f"Datos ficticios creados: usuario {resultado['usuario']}; paciente {resultado['codigo_paciente']}.")
    print(f'Clave de acceso guardada SOLO en tu equipo: {destino}')
    print('Léela con Get-Content y elimina el archivo cuando ya no lo necesites.')


if __name__ == '__main__':
    asyncio.run(main())
