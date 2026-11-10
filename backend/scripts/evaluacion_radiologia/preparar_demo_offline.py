"""Semilla ficticia en base vacía de evaluación, nunca en instalación normal."""
import asyncio
import hashlib
from pathlib import Path
import secrets
from sqlalchemy import text
from sqlalchemy.engine import make_url
from app.config.settings import settings
from app.config.database import SessionLocal, engine
from app.accesos.infrastructure.security.password_hasher import Argon2PasswordHasher
from scripts.preparar_medico_demo import preparar_medico_demo
from scripts.preparar_estudio_imagen_demo import preparar_estudio_demo


async def main():
    u = make_url(settings.database_url)
    if u.host != '127.0.0.1' or not u.database.startswith('fase5_'):
        raise RuntimeError('Solo base temporal fase5_ en loopback aislado')
    imagen = Path('/samples/NIH-RX-001.png').read_bytes()
    async with SessionLocal.begin() as db:
        await preparar_medico_demo(db, Argon2PasswordHasher().hashear(secrets.token_urlsafe(32)))
        usuario = await db.scalar(text("SELECT id FROM public.usuario WHERE identificador_acceso='medico_demo'"))
        await preparar_estudio_demo(db, usuario, {'url_archivo': 'NIH-RX-001.png',
            'tamano_bytes': len(imagen), 'hash_sha256': hashlib.sha256(imagen).hexdigest()})
    await engine.dispose()
    print('Datos de evaluación ficticios nuevos creados en base aislada.')


if __name__ == '__main__':
    asyncio.run(main())
