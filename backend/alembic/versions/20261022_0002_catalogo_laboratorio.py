"""Prepara plantillas de laboratorio y captura estructurada.

No carga catálogos clínicos: los nombres y valores deben validarse con el
servicio antes de poblar las plantillas.
"""

from alembic import op
import sqlalchemy as sa

revision = "20261022_0002"
down_revision = "20261022_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tipo_estudio",
        sa.Column("plantilla_examen_id", sa.BigInteger(), nullable=True),
        schema="public",
    )
    op.create_foreign_key(
        "fk_tipo_estudio_plantilla_examen",
        "tipo_estudio",
        "plantilla_examen",
        ["plantilla_examen_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_tipo_estudio_plantilla_examen_id",
        "tipo_estudio",
        ["plantilla_examen_id"],
        schema="public",
    )

    # Una plantilla puede dejar la precisión sin especificar hasta que el
    # laboratorio confirme cuántos decimales utiliza en cada campo.
    op.add_column(
        "parametro_plantilla",
        sa.Column("precision_decimal", sa.SmallInteger(), nullable=True),
        schema="public",
    )
    op.create_check_constraint(
        "ck_parametro_precision_decimal",
        "parametro_plantilla",
        "precision_decimal IS NULL OR precision_decimal >= 0",
        schema="public",
    )

    op.create_table(
        "opcion_parametro",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("parametro_id", sa.BigInteger(), nullable=False),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("etiqueta", sa.Text(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_opcion_parametro"),
        sa.ForeignKeyConstraint(
            ["parametro_id"],
            ["public.parametro_plantilla.id"],
            name="fk_opcion_parametro_parametro",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "parametro_id", "codigo", name="uq_opcion_parametro_codigo"
        ),
        sa.CheckConstraint("length(btrim(codigo)) > 0", name="ck_opcion_codigo_no_vacio"),
        sa.CheckConstraint(
            "length(btrim(etiqueta)) > 0", name="ck_opcion_etiqueta_no_vacia"
        ),
        schema="public",
    )
    op.create_index(
        "ix_opcion_parametro_parametro_orden",
        "opcion_parametro",
        ["parametro_id", "orden"],
        schema="public",
    )

    # La plantilla almacena sus referencias como estaban vigentes al publicarse.
    # La muestra puede ser configurada por código una vez validados los tipos
    # usados por el hospital; se deja opcional y sin catálogo inventado.
    op.add_column(
        "muestra",
        sa.Column("tipo_muestra", sa.Text(), nullable=True),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column("muestra", "tipo_muestra", schema="public")
    op.drop_index(
        "ix_opcion_parametro_parametro_orden",
        table_name="opcion_parametro",
        schema="public",
    )
    op.drop_table("opcion_parametro", schema="public")
    op.drop_constraint(
        "ck_parametro_precision_decimal",
        "parametro_plantilla",
        schema="public",
        type_="check",
    )
    op.drop_column("parametro_plantilla", "precision_decimal", schema="public")
    op.drop_index(
        "ix_tipo_estudio_plantilla_examen_id",
        table_name="tipo_estudio",
        schema="public",
    )
    op.drop_constraint(
        "fk_tipo_estudio_plantilla_examen",
        "tipo_estudio",
        schema="public",
        type_="foreignkey",
    )
    op.drop_column("tipo_estudio", "plantilla_examen_id", schema="public")
