"""Crea una cuenta y trabajador ficticios para probar el módulo de enfermería.

Uso desde backend: python -m scripts.preparar_enfermera_demo
Se detiene si ya existe la cuenta o si el identificador reservado pertenece a otra persona.
"""
import asyncio
from getpass import getpass

from sqlalchemy import text

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import SessionLocal, engine

IDENTIFICADOR = 'enfermera_demo'
TRABAJADOR_IDENTIFICADOR = 'T-DEMO-ENF-001'
TRABAJADOR_NOMBRE = 'Usuario ficticio de enfermería'


async def preparar(password_hash: str):
    async with SessionLocal.begin() as db:
        existente = (await db.execute(text('''
            SELECT id FROM public.usuario WHERE identificador_acceso = :identificador
        '''), {'identificador': IDENTIFICADOR})).scalar_one_or_none()
        if existente is not None:
            raise ValueError('La cuenta enfermera_demo ya existe; no se modificó.')

        rol_id = (await db.execute(text('''
            SELECT id FROM public.rol WHERE codigo = 'enfermeria' AND activo = true
        '''))).scalar_one_or_none()
        if rol_id is None:
            raise ValueError('No existe el rol enfermeria activo. Aplica las migraciones primero.')

        trabajador = (await db.execute(text('''
            SELECT id, estado, nombre_completo FROM public.trabajador
            WHERE identificador = :identificador
        '''), {'identificador': TRABAJADOR_IDENTIFICADOR})).mappings().one_or_none()
        if trabajador is None:
            trabajador_id = (await db.execute(text('''
                INSERT INTO public.trabajador
                    (identificador, nombre_completo, estado, fecha_inicio)
                VALUES (:identificador, :nombre, 'activo', CURRENT_DATE) RETURNING id
            '''), {'identificador': TRABAJADOR_IDENTIFICADOR,
                  'nombre': TRABAJADOR_NOMBRE})).scalar_one()
            await db.execute(text('''
                INSERT INTO public.trabajador_estado_historial
                    (trabajador_id, estado, fecha_vigencia)
                VALUES (:id, 'activo', CURRENT_DATE)
            '''), {'id': trabajador_id})
        else:
            if (trabajador['estado'] != 'activo'
                    or trabajador['nombre_completo'] != TRABAJADOR_NOMBRE):
                raise ValueError('El trabajador reservado existe con otros datos; no se modificó.')
            trabajador_id = trabajador['id']

        await db.execute(text('''
            INSERT INTO public.usuario
                (identificador_acceso, contrasena_hash, rol_id, trabajador_id, estado)
            VALUES (:identificador, :hash, :rol, :trabajador, 'activo')
        '''), {'identificador': IDENTIFICADOR, 'hash': password_hash,
              'rol': rol_id, 'trabajador': trabajador_id})
    return 'Cuenta ficticia enfermera_demo creada.'


def main():
    engine.echo = False
    clave = getpass('Contraseña de prueba: ')
    if not clave or clave != getpass('Repite la contraseña: '):
        raise SystemExit('La contraseña está vacía o no coincide.')
    password_hash = Argon2PasswordHasher().hashear(clave)
    print(asyncio.run(preparar(password_hash)))


if __name__ == '__main__':
    main()
