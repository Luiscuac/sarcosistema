"""Crea una cuenta ficticia de enfermería con contraseña interactiva."""
import asyncio
from getpass import getpass

from sqlalchemy import text

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import SessionLocal, engine


async def preparar(identificador: str, password_hash: str):
    async with SessionLocal.begin() as db:
        existente = (await db.execute(text(
            "SELECT id FROM public.usuario WHERE identificador_acceso=:identificador"
        ), {"identificador": identificador})).scalar_one_or_none()
        if existente is not None:
            raise ValueError("La cuenta ya existe; no se modificó.")

        rol = (await db.execute(text(
            "SELECT id FROM public.rol WHERE codigo='enfermeria' AND activo=true"
        ))).scalar_one_or_none()
        if rol is None:
            raise ValueError("No existe el rol enfermeria activo; aplica las migraciones.")

        trabajador_id = (await db.execute(text("""
            SELECT id FROM public.trabajador WHERE identificador='T-DEMO-ENF-001'
        """))).scalar_one_or_none()
        if trabajador_id is None:
            trabajador_id = (await db.execute(text("""
                INSERT INTO public.trabajador
                    (identificador,nombre_completo,estado,fecha_inicio)
                VALUES ('T-DEMO-ENF-001','Usuario demo enfermeria','activo',CURRENT_DATE)
                RETURNING id
            """))).scalar_one()
            await db.execute(text("""
                INSERT INTO public.trabajador_estado_historial
                    (trabajador_id,estado,fecha_vigencia)
                VALUES (:id,'activo',CURRENT_DATE)
            """), {"id": trabajador_id})
        else:
            estado = (await db.execute(text(
                "SELECT estado FROM public.trabajador WHERE id=:id"
            ), {"id": trabajador_id})).scalar_one()
            if estado != "activo":
                raise ValueError("El trabajador de demostración existente no está activo.")

        await db.execute(text("""
            INSERT INTO public.usuario
                (identificador_acceso,contrasena_hash,rol_id,trabajador_id,estado)
            VALUES (:identificador,:hash,:rol,:trabajador,'activo')
        """), {"identificador": identificador, "hash": password_hash,
               "rol": rol, "trabajador": trabajador_id})


def main():
    identificador = input("Usuario ficticio de enfermería: ").strip()
    if not identificador:
        raise SystemExit("El identificador es obligatorio.")
    engine.echo = False
    password = getpass("Contraseña de prueba: ")
    if not password or password != getpass("Repite la contraseña: "):
        raise SystemExit("La contraseña está vacía o no coincide.")
    hashed = Argon2PasswordHasher().hashear(password)
    asyncio.run(preparar(identificador, hashed))
    print("Cuenta ficticia de enfermería creada.")


if __name__ == "__main__":
    main()
