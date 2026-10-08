import asyncio
from app.config.database import SessionLocal
from app.accesos.models import Usuario, Rol
from app.accesos.security import hashear_password
from sqlalchemy import select, insert, text

async def seed_user():
    async with SessionLocal() as db:
        # Asegurarse de que exista el rol 'laboratorio'
        result = await db.execute(select(Rol).where(Rol.codigo == 'laboratorio'))
        rol = result.scalar_one_or_none()
        
        if not rol:
            print("Rol 'laboratorio' no encontrado, intentando crearlo (sin forzar ID)...")
            result = await db.execute(
                text("INSERT INTO public.rol (codigo, nombre, descripcion, activo) VALUES ('laboratorio', 'Personal de Laboratorio', 'Rol para personal de laboratorio', true) RETURNING id;")
            )
            rol_id = result.scalar()
        else:
            rol_id = rol.id

        # Insertar un trabajador ficticio
        result = await db.execute(text("SELECT id FROM public.trabajador WHERE identificador = 'T-999';"))
        trabajador_id = result.scalar()

        if not trabajador_id:
            result = await db.execute(
                text("INSERT INTO public.trabajador (identificador, nombre_completo, estado, fecha_inicio) VALUES ('T-999', 'Usuario Pruebas', 'activo', '2026-01-01') RETURNING id;")
            )
            trabajador_id = result.scalar()

        # Crear el usuario
        result = await db.execute(select(Usuario).where(Usuario.identificador_acceso == 'lab_test'))
        usuario_existente = result.scalar_one_or_none()

        if usuario_existente:
            print("El usuario 'lab_test' ya existe.")
            return

        nuevo_usuario = Usuario(
            identificador_acceso="lab_test",
            contrasena_hash=hashear_password("secreta123"),
            rol_id=rol_id,
            trabajador_id=trabajador_id,
            estado="activo"
        )
        db.add(nuevo_usuario)
        await db.commit()
        print("Usuario 'lab_test' (contraseña: secreta123) creado exitosamente.")

if __name__ == "__main__":
    asyncio.run(seed_user())
