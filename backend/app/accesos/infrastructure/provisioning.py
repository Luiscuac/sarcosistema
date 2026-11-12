"""Alta de cuentas hospitalarias desde una sesión administrativa del servidor."""
import argparse
import asyncio
from getpass import getpass
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.config.database import SessionLocal, engine

ROLES_PERMITIDOS = frozenset({"medico", "laboratorio", "enfermeria"})
LONGITUD_MINIMA_CLAVE = 12


async def crear_cuenta(
    db: AsyncSession,
    identificador: str,
    trabajador_id: int,
    rol: str,
    contrasena_hash: str,
) -> int:
    identificador = identificador.strip()
    if not identificador or len(identificador) > 100:
        raise ValueError("El identificador debe tener entre 1 y 100 caracteres.")
    if rol not in ROLES_PERMITIDOS:
        raise ValueError("El rol no está habilitado para el despliegue hospitalario.")

    existente = (await db.execute(
        text("SELECT id FROM public.usuario WHERE identificador_acceso = :identificador"),
        {"identificador": identificador},
    )).scalar_one_or_none()
    if existente is not None:
        raise ValueError("La cuenta ya existe; no se modificó.")

    trabajador_activo = (await db.execute(
        text("""
            SELECT id FROM public.trabajador
            WHERE id = :trabajador_id AND estado = 'activo'
        """),
        {"trabajador_id": trabajador_id},
    )).scalar_one_or_none()
    if trabajador_activo is None:
        raise ValueError("El ID debe pertenecer a un trabajador activo.")

    if rol == "medico":
        medico_activo = (await db.execute(
            text("""
                SELECT id FROM public.medico
                WHERE trabajador_id = :trabajador_id AND activo = true
            """),
            {"trabajador_id": trabajador_id},
        )).scalar_one_or_none()
        if medico_activo is None:
            raise ValueError("El trabajador no tiene un registro médico activo.")

    rol_id = (await db.execute(
        text("SELECT id FROM public.rol WHERE codigo = :rol AND activo = true"),
        {"rol": rol},
    )).scalar_one_or_none()
    if rol_id is None:
        raise ValueError(f"No existe un rol {rol} activo.")

    return (await db.execute(
        text("""
            INSERT INTO public.usuario
                (identificador_acceso, contrasena_hash, rol_id, trabajador_id, estado)
            VALUES (:identificador, :hash, :rol_id, :trabajador_id, 'activo')
            RETURNING id
        """),
        {
            "identificador": identificador,
            "hash": contrasena_hash,
            "rol_id": rol_id,
            "trabajador_id": trabajador_id,
        },
    )).scalar_one()


async def _crear_con_transaccion(
    identificador: str,
    trabajador_id: int,
    rol: str,
    contrasena_hash: str,
) -> int:
    async with SessionLocal.begin() as db:
        return await crear_cuenta(db, identificador, trabajador_id, rol, contrasena_hash)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identificador", help="identificador de acceso del trabajador")
    parser.add_argument("--trabajador-id", type=int, required=True, help="ID de un trabajador activo")
    parser.add_argument("--rol", choices=sorted(ROLES_PERMITIDOS), required=True)
    parser.add_argument("--operador", required=True, help="identificador del administrador responsable")
    parser.add_argument("--referencia", required=True, help="ticket o referencia de autorización")
    args = parser.parse_args()

    clave = getpass("Contraseña inicial: ")
    if len(clave) < LONGITUD_MINIMA_CLAVE:
        parser.error(f"La contraseña debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres.")
    if clave != getpass("Repite la contraseña: "):
        parser.error("Las contraseñas no coinciden.")

    engine.echo = False
    contrasena_hash = Argon2PasswordHasher().hashear(clave)
    try:
        usuario_id = asyncio.run(_crear_con_transaccion(
            args.identificador, args.trabajador_id, args.rol, contrasena_hash,
        ))
    except ValueError as error:
        parser.error(str(error))

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info(
        "Alta de cuenta: usuario_id=%s rol=%s trabajador_id=%s operador=%s referencia=%s",
        usuario_id, args.rol, args.trabajador_id, args.operador, args.referencia,
    )
    print(f"Cuenta creada: usuario_id={usuario_id}, rol={args.rol}.")


if __name__ == "__main__":
    main()
