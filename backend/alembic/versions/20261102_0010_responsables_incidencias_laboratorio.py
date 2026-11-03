"""Guarda responsables declarados e incidencias de muestras pendientes."""

from alembic import op
import sqlalchemy as sa


revision = "20261102_0010"
down_revision = "20261102_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("muestra", sa.Column("responsable_recepcion", sa.Text(), nullable=True), schema="public")
    op.add_column("resultado_laboratorio", sa.Column("responsable_analisis", sa.Text(), nullable=True), schema="public")
    op.add_column("version_resultado", sa.Column("responsable_publicacion", sa.Text(), nullable=True), schema="public")
    op.create_table(
        "incidencia_muestra",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("estudio_id", sa.BigInteger(), sa.ForeignKey("public.estudio_solicitado.id"), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("responsable", sa.Text(), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("usuario_id", sa.BigInteger(), sa.ForeignKey("public.usuario.id"), nullable=False),
        sa.CheckConstraint("motivo IN ('muestra_no_entregada', 'toma_rechazada', 'toma_no_realizada')", name="ck_incidencia_muestra_motivo"),
        schema="public",
    )
    op.create_index("ix_incidencia_muestra_estudio_fecha", "incidencia_muestra", ["estudio_id", "fecha_hora"], schema="public")


def downgrade() -> None:
    raise RuntimeError(
        "La migración 20261102_0010 contiene datos de trazabilidad clínica y "
        "no admite downgrade automático."
    )
