"""Crea una cuenta ficticia exclusiva para el personal de Rayos X.

Uso desde backend:
  python -m scripts.preparar_rayos_x_demo
"""
import asyncio
from getpass import getpass

from sqlalchemy import text

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import SessionLocal, engine


async def preparar(identificador: str, password_hash: str) -> None:
    async with SessionLocal.begin() as db:
        existente = await db.scalar(text(
            "SELECT id FROM public.usuario WHERE identificador_acceso=:identificador"
        ), {'identificador': identificador})
        if existente is not None:
            raise ValueError('La cuenta ya existe; no se modificó.')

        rol = await db.scalar(text(
            "SELECT id FROM public.rol WHERE codigo='rayos_x' AND activo=true"
        ))
        if rol is None:
            raise ValueError('No existe el rol rayos_x activo; aplica las migraciones.')

        trabajador_id = await db.scalar(text(
            "SELECT id FROM public.trabajador WHERE identificador='T-DEMO-RX-001'"
        ))
        if trabajador_id is None:
            trabajador_id = await db.scalar(text("""
                INSERT INTO public.trabajador
                    (identificador,nombre_completo,estado,fecha_inicio)
                VALUES ('T-DEMO-RX-001','Usuario demo de Rayos X','activo',CURRENT_DATE)
                RETURNING id
            """))
            await db.execute(text("""
                INSERT INTO public.trabajador_estado_historial
                    (trabajador_id,estado,fecha_vigencia)
                VALUES (:id,'activo',CURRENT_DATE)
            """), {'id': trabajador_id})
        else:
            trabajador = (await db.execute(text(
                'SELECT estado,nombre_completo FROM public.trabajador WHERE id=:id'
            ), {'id': trabajador_id})).mappings().one()
            if trabajador['estado'] != 'activo' or trabajador['nombre_completo'] != 'Usuario demo de Rayos X':
                raise ValueError('El identificador reservado de demostración ya tiene otros datos; no se modificó.')

        await db.execute(text("""
            INSERT INTO public.usuario
                (identificador_acceso,contrasena_hash,rol_id,trabajador_id,estado)
            VALUES (:identificador,:hash,:rol,:trabajador,'activo')
        """), {'identificador': identificador, 'hash': password_hash,
               'rol': rol, 'trabajador': trabajador_id})


def main() -> None:
    identificador = input('Usuario ficticio de Rayos X: ').strip()
    if not identificador:
        raise SystemExit('El identificador es obligatorio.')
    engine.echo = False
    password = getpass('Contraseña de prueba: ')
    if not password or password != getpass('Repite la contraseña: '):
        raise SystemExit('La contraseña está vacía o no coincide.')
    password_hash = Argon2PasswordHasher().hashear(password)
    asyncio.run(preparar(identificador, password_hash))
    print('Cuenta ficticia de Rayos X creada.')


if __name__ == '__main__':
    main()
