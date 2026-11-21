"""Confirmación de tuberculosis registrada por el médico en la revisión de la IA.

Columna opcional y aditiva (como anormal_confirmado). Permite calibrar el corte del aviso
"patrón compatible con TB" con casos del propio hospital. Las revisiones siguen siendo históricas.
"""

from alembic import op


revision = '20261121_0022'
down_revision = '20261117_0021'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE public.imagen_revision_ia ADD COLUMN tb_confirmada boolean')
    op.execute("COMMENT ON COLUMN public.imagen_revision_ia.tb_confirmada IS "
               "'TB según el médico con confirmación bacteriológica (baciloscopía, GeneXpert, cultivo): true confirmada, "
               "false descartada, NULL sin dato. No es un diagnóstico publicado.'")


def downgrade():
    raise RuntimeError('No eliminar la confirmación médica registrada automáticamente.')
