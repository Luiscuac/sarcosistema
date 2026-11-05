"""El Compose debe conectar backend a la red interna, no al localhost del host."""
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlsplit

import pytest


@pytest.mark.skipif(shutil.which('docker') is None, reason='Requiere Docker Compose CLI para validar la configuración')
def test_compose_sobrescribe_database_url_local_sin_exponer_secretos(tmp_path):
    repo = Path(__file__).resolve().parents[4]
    compose = tmp_path / 'compose.yml'
    compose.write_text((repo / 'docker-compose.yml').read_text(encoding='utf-8'), encoding='utf-8')
    (tmp_path / 'backend').mkdir()
    (tmp_path / 'backend' / '.env').write_text(
        'DATABASE_URL=postgresql+asyncpg://ficticio:ficticio@localhost:5432/base_ficticia\n'
        'JWT_SECRET_KEY=clave-ficticia-compose\n', encoding='utf-8')
    resultado = subprocess.run(['docker', 'compose', '-f', str(compose), 'config', '--format', 'json'],
        capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, 'Docker Compose no pudo resolver la configuración de prueba'
    configuracion = json.loads(resultado.stdout)
    destino = urlsplit(configuracion['services']['backend']['environment']['DATABASE_URL'])
    assert destino.hostname == 'db'
    assert destino.port == 5432
