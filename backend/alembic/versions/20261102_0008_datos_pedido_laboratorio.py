"""Añade teléfono del paciente y procedencia del pedido de laboratorio."""

from alembic import op
import sqlalchemy as sa


revision = "20261102_0008"
down_revision = "20261027_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("paciente", sa.Column("telefono", sa.Text(), nullable=True), schema="public")
    op.add_column(
        "solicitud",
        sa.Column("procedencia", sa.Text(), nullable=False, server_default="este_centro"),
        schema="public",
    )
    op.create_check_constraint(
        "ck_solicitud_procedencia",
        "solicitud",
        "procedencia IN ('este_centro', 'otro_centro')",
        schema="public",
    )


def downgrade() -> None:
    op.drop_constraint("ck_solicitud_procedencia", "solicitud", schema="public")
    op.drop_column("solicitud", "procedencia", schema="public")
    op.drop_column("paciente", "telefono", schema="public")
