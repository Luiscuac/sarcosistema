"""Marca el esquema bootstrap del proyecto como linea base de Alembic.

La estructura existente se crea desde database/schema.sql en una base nueva.
Las bases que ya tienen ese esquema pueden avanzar con las migraciones
incrementales sin volver a ejecutar el archivo bootstrap.
"""

from alembic import op
import sqlalchemy as sa

revision = "20261022_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    required_tables = (
        "paciente",
        "solicitud",
        "estudio_solicitado",
        "tipo_estudio",
        "plantilla_examen",
        "plantilla_examen_version",
        "parametro_plantilla",
        "resultado_laboratorio",
        "version_resultado",
        "detalle_valor_resultado",
    )
    missing = [
        table
        for table in required_tables
        if bind.execute(
            sa.text("SELECT to_regclass(:qualified_name)"),
            {"qualified_name": f"public.{table}"},
        ).scalar_one()
        is None
    ]
    if missing:
        raise RuntimeError(
            "La base no contiene el esquema SarcoSistema esperado. "
            "Inicializa una base de desarrollo con el procedimiento del proyecto "
            "antes de aplicar Alembic; no ejecutes schema.sql sobre una base con datos. "
            f"Faltan tablas: {', '.join(missing)}"
        )


def downgrade() -> None:
    # La revision solo marca el esquema base y no modifica objetos.
    pass
