"""La migración no debe ocultar asignaciones duplicadas ni borrar historia."""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def cargar_migracion():
    archivo = Path(__file__).resolve().parents[1] / 'alembic' / 'versions' / '20261027_0007_consultas_medicas.py'
    spec = importlib.util.spec_from_file_location('migracion_consultas', archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_migracion_rechaza_especialidades_duplicadas_sin_borrar_filas():
    migracion = cargar_migracion()
    bind = MagicMock()
    bind.execute.return_value.first.return_value = (17, 2)
    migracion.op.get_bind = lambda: bind
    migracion.op.add_column = MagicMock()

    with pytest.raises(RuntimeError, match='17'):
        migracion.upgrade()

    assert not migracion.op.add_column.called


def test_migracion_agrega_vigencia_y_clave_sin_alterar_consultas_existentes():
    migracion = cargar_migracion()
    bind = MagicMock()
    bind.execute.return_value.first.return_value = None
    migracion.op.get_bind = lambda: bind
    migracion.op.add_column = MagicMock()
    migracion.op.create_unique_constraint = MagicMock()
    migracion.op.create_foreign_key = MagicMock()
    migracion.op.alter_column = MagicMock()

    migracion.upgrade()

    assert [call.args[0] for call in migracion.op.add_column.call_args_list] == [
        'medico_especialidad', 'consulta', 'consulta'
    ]
    assert any('medico_id' in str(call) for call in migracion.op.create_unique_constraint.call_args_list)
    assert all('DELETE' not in str(call).upper() for call in bind.execute.call_args_list)
