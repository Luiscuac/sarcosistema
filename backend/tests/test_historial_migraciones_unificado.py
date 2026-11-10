"""El merge conserva ambos historiales sin repetir DDL ni permitir downgrade."""
from pathlib import Path
from hashlib import sha256
import subprocess

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory


BACKEND = Path(__file__).resolve().parents[1]
MAIN_ORIGEN = '68625b83eeed5e1eb9f044e6c360f0c4d4ce5f13'
ARCHIVOS_MAIN = (
    '20261102_0008_datos_pedido_laboratorio.py',
    '20261102_0009_parametros_validados_laboratorio.py',
    '20261102_0010_responsables_incidencias_laboratorio.py',
    '20261103_0011_estudios_no_realizados.py',
)
# Verificados byte por byte contra MAIN_ORIGEN durante la reconciliacion.
SHA256_MAIN = dict(zip(ARCHIVOS_MAIN, (
    '3255ebd3b7fa72a962eb1ed995d8191a670fe24227572c6f6775fd7530f6f9a4',
    '062e84905ec58968f58d5e22ee214927a4da050925d3c1ba91252fbf9f472ce2',
    '5d449c0dabb9138083aab65a84d9f205b323b0853a835e50ece87cc88ba0f671',
    '87eaa2d56d2c24fd10a38c9a0c09e87f4c23ea7fb67eaa55da2f7060a269cfc2',
)))


def historial():
    config = Config(str(BACKEND / 'alembic.ini'))
    config.set_main_option('script_location', str(BACKEND / 'alembic'))
    return ScriptDirectory.from_config(config)


def test_una_cabeza_conserva_ambas_ramas():
    scripts = historial()
    assert scripts.get_heads() == ['20261109_0012']
    ancestros = {r.revision for r in scripts.walk_revisions()}
    assert {'20261103_0011', '20261103_0009', '20261027_0007'} <= ancestros
    merge = scripts.get_revision('20261109_0012')
    assert set(merge.down_revision) == {'20261103_0011', '20261103_0009'}


@pytest.mark.parametrize('nombre', ARCHIVOS_MAIN)
def test_migraciones_main_identicas_al_origen(nombre, monkeypatch):
    def sin_historial_git(*args, **kwargs):
        raise RuntimeError('Checkout superficial: commit historico no disponible')

    monkeypatch.setattr(subprocess, 'check_output', sin_historial_git)
    archivo = BACKEND / 'alembic' / 'versions' / nombre
    assert archivo.exists(), f'Falta migracion de main: {nombre}'
    # Normalizar solo saltos de checkout Windows; no requerir objetos Git en CI.
    contenido = archivo.read_bytes().replace(b'\r\n', b'\n')
    assert sha256(contenido).hexdigest() == SHA256_MAIN[nombre]


def test_merge_no_ejecuta_ddl_y_bloquea_downgrade():
    scripts = historial()
    assert scripts.get_heads() == ['20261109_0012']
    modulo = scripts.get_revision('20261109_0012').module
    # Sin contexto Alembic: cualquier operacion DDL fallaria aqui.
    assert modulo.upgrade() is None
    with pytest.raises(RuntimeError, match='reconciliacion'):
        modulo.downgrade()
