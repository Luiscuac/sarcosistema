"""Prepara una cuenta ficticia de laboratorio sin exponer la contraseña en argumentos.

Uso desde backend:
  python -m scripts.preparar_usuario_prueba laboratorio_prueba --trabajador-id 123
Para una cuenta ya existente, omitir --trabajador-id y se actualizará su hash.
"""
import argparse
import asyncio
from getpass import getpass

from sqlalchemy import text

from app.accesos.security import hashear_password
from app.config.database import SessionLocal


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

        if trabajador_id is None:
            raise ValueError("La cuenta no existe; indica --trabajador-id de un trabajador ficticio activo")

        rol = (await db.execute(text("""
            SELECT id FROM public.rol WHERE codigo = 'laboratorio' AND activo = true
        """))).scalar_one_or_none()
        trabajador = (await db.execute(text("""
            SELECT id FROM public.trabajador WHERE id = :id AND estado = 'activo'
        """), {"id": trabajador_id})).scalar_one_or_none()
        if rol is None or trabajador is None:
            raise ValueError("Se requiere el rol laboratorio y un trabajador activo existentes")

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
    parser.add_argument("--trabajador-id", type=int, help="solo al crear una cuenta nueva")
    args = parser.parse_args()
    password = getpass("Contraseña de prueba: ")
    if not password or password != getpass("Repite la contraseña: "):
        raise SystemExit("La contraseña está vacía o no coincide")
    print(asyncio.run(preparar(args.identificador, args.trabajador_id, hashear_password(password))))


if __name__ == "__main__":
    main()
