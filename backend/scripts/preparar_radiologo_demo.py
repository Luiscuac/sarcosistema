"""Crea una cuenta ficticia de médico radiólogo (rol `radiologo`): redacta y valida informes de Rayos X.

Uso desde backend:
  python -m scripts.preparar_radiologo_demo                      # pide usuario y contraseña
  python -m scripts.preparar_radiologo_demo radiologo_prueba --generar-clave
      # genera una clave aleatoria y la guarda SOLO en un archivo local fuera del repositorio

No modifica cuentas existentes. Solo contra PostgreSQL local.
"""
import argparse
import asyncio
import os
import secrets
from getpass import getpass
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import SessionLocal, engine
from app.config.settings import settings

TRABAJADOR = 'T-DEMO-RADIOLOGO-001'
NOMBRE = 'Radiólogo demo (SOLO PRUEBA)'


async def preparar(identificador: str, password_hash: str) -> None:
    async with SessionLocal.begin() as db:
        if await db.scalar(text('SELECT id FROM public.usuario WHERE identificador_acceso=:i'), {'i': identificador}) is not None:
            raise ValueError('La cuenta ya existe; no se modificó.')
        rol = await db.scalar(text("SELECT id FROM public.rol WHERE codigo='radiologo' AND activo=true"))
        if rol is None:
            raise ValueError('No existe el rol radiologo activo; aplica las migraciones (alembic upgrade head).')
        trabajador = (await db.execute(text('SELECT id, estado, nombre_completo FROM public.trabajador WHERE identificador=:i'),
                                       {'i': TRABAJADOR})).mappings().one_or_none()
        if trabajador is None:
            trabajador_id = await db.scalar(text("""INSERT INTO public.trabajador (identificador,nombre_completo,estado,fecha_inicio)
                VALUES (:i,:n,'activo',CURRENT_DATE) RETURNING id"""), {'i': TRABAJADOR, 'n': NOMBRE})
            await db.execute(text("""INSERT INTO public.trabajador_estado_historial (trabajador_id,estado,fecha_vigencia)
                VALUES (:id,'activo',CURRENT_DATE)"""), {'id': trabajador_id})
        elif trabajador['estado'] != 'activo' or trabajador['nombre_completo'] != NOMBRE:
            raise ValueError('El identificador reservado de demostración ya tiene otros datos; no se modificó.')
        else:
            trabajador_id = trabajador['id']
        await db.execute(text("""INSERT INTO public.usuario (identificador_acceso,contrasena_hash,rol_id,trabajador_id,estado)
            VALUES (:i,:h,:r,:t,'activo')"""), {'i': identificador, 'h': password_hash, 'r': rol, 't': trabajador_id})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('usuario', nargs='?')
    parser.add_argument('--generar-clave', action='store_true')
    args = parser.parse_args()
    if make_url(settings.database_url).host not in ('localhost', '127.0.0.1'):
        raise SystemExit('Este preparador solo se permite contra PostgreSQL local.')
    identificador = (args.usuario or input('Usuario ficticio de radiólogo: ')).strip()
    if not identificador:
        raise SystemExit('El identificador es obligatorio.')
    engine.echo = False
    destino = None
    if args.generar_clave:
        password = secrets.token_urlsafe(14)
        carpeta = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))) / 'Temp' / 'sarcosistema'
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / f'{identificador}_clave_{secrets.token_hex(4)}.txt'
    else:
        password = getpass('Contraseña de prueba: ')
        if not password or password != getpass('Repite la contraseña: '):
            raise SystemExit('La contraseña está vacía o no coincide.')
    asyncio.run(preparar(identificador, Argon2PasswordHasher().hashear(password)))
    print(f'Cuenta ficticia de radiólogo creada: {identificador}')
    if destino:
        destino.write_text(password, encoding='utf-8')
        print(f'Clave guardada SOLO en tu equipo: {destino}')


if __name__ == '__main__':
    main()
