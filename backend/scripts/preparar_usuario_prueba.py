"""Prepara una cuenta ficticia de laboratorio con una contraseña interactiva.

Uso desde backend:
  python -m scripts.preparar_usuario_prueba laboratorio_prueba
Por defecto crea un trabajador de demostración si hace falta. También se puede
usar --trabajador-id para vincularla a un trabajador ficticio ya existente.
"""
import argparse
import asyncio
from getpass import getpass

from sqlalchemy import text

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import SessionLocal, engine

IDENTIFICADOR_TRABAJADOR_PRUEBA = "T-DEMO-LAB-001"
NOMBRE_TRABAJADOR_PRUEBA = "Usuario de demostración de laboratorio"


async def preparar(identificador: str, trabajador_id: int | None, password_hash: str):
    async with SessionLocal.begin() as db:
        usuario = (await db.execute(
            text("""
                SELECT u.id, u.estado, r.codigo AS rol, r.activo AS rol_activo,
                       t.estado AS trabajador_estado
                FROM public.usuario AS u
                JOIN public.rol AS r ON r.id = u.rol_id
                JOIN public.trabajador AS t ON t.id = u.trabajador_id
                WHERE u.identificador_acceso = :identificador
            """),
            {"identificador": identificador},
        )).mappings().one_or_none()

        if usuario is not None:
            if trabajador_id is not None:
                raise ValueError("La cuenta ya existe; omite --trabajador-id para renovar su contraseña")
            if (usuario["estado"] != "activo" or usuario["rol"] != "laboratorio"
                    or not usuario["rol_activo"] or usuario["trabajador_estado"] != "activo"):
                raise ValueError("La cuenta existente debe estar activa y pertenecer a laboratorio")
            await db.execute(text("""
                UPDATE public.usuario SET contrasena_hash = :hash, updated_at = now()
                WHERE id = :id
            """), {"hash": password_hash, "id": usuario["id"]})
            return "Contraseña de la cuenta existente actualizada."

        rol = (await db.execute(text("""
            SELECT id FROM public.rol WHERE codigo = 'laboratorio' AND activo = true
        """))).scalar_one_or_none()
        if rol is None:
            raise ValueError("No existe un rol laboratorio activo en la base")

        if trabajador_id is None:
            trabajador = (await db.execute(text("""
                SELECT id, estado, nombre_completo FROM public.trabajador
                WHERE identificador = :identificador
            """), {"identificador": IDENTIFICADOR_TRABAJADOR_PRUEBA})).mappings().one_or_none()
            if trabajador is None:
                trabajador_id = (await db.execute(text("""
                    INSERT INTO public.trabajador
                        (identificador, nombre_completo, estado, fecha_inicio)
                    VALUES (:identificador, :nombre, 'activo', CURRENT_DATE)
                    RETURNING id
                """), {
                    "identificador": IDENTIFICADOR_TRABAJADOR_PRUEBA,
                    "nombre": NOMBRE_TRABAJADOR_PRUEBA,
                })).scalar_one()
                await db.execute(text("""
                    INSERT INTO public.trabajador_estado_historial
                        (trabajador_id, estado, fecha_vigencia)
                    VALUES (:trabajador_id, 'activo', CURRENT_DATE)
                """), {"trabajador_id": trabajador_id})
            else:
                if (trabajador["estado"] != "activo"
                        or trabajador["nombre_completo"] != NOMBRE_TRABAJADOR_PRUEBA):
                    raise ValueError(
                        "El identificador reservado para demostración ya existe con otros datos; "
                        "no se modificó"
                    )
                trabajador_id = trabajador["id"]
        else:
            trabajador = (await db.execute(text("""
                SELECT id FROM public.trabajador WHERE id = :id AND estado = 'activo'
            """), {"id": trabajador_id})).scalar_one_or_none()
            if trabajador is None:
                raise ValueError("El ID debe pertenecer a un trabajador activo")

        await db.execute(text("""
            INSERT INTO public.usuario
                (identificador_acceso, contrasena_hash, rol_id, trabajador_id, estado)
            VALUES (:identificador, :hash, :rol_id, :trabajador_id, 'activo')
        """), {
            "identificador": identificador, "hash": password_hash,
            "rol_id": rol, "trabajador_id": trabajador_id,
        })
        return "Cuenta de prueba creada."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identificador", help="identificador de acceso ficticio")
    parser.add_argument("--trabajador-id", type=int, help="ID de un trabajador ficticio activo existente")
    args = parser.parse_args()
    # Evita que SQLAlchemy imprima parámetros sensibles (incluido el hash) con DEBUG=true.
    engine.echo = False
    password = getpass("Contraseña de prueba: ")
    if not password or password != getpass("Repite la contraseña: "):
        raise SystemExit("La contraseña está vacía o no coincide")
    password_hash = Argon2PasswordHasher().hashear(password)
    print(asyncio.run(preparar(args.identificador, args.trabajador_id, password_hash)))


if __name__ == "__main__":
    main()
