"""Lectura estructurada del médico en la revisión de la IA: ¿radiografía anormal?

Columna opcional y aditiva. Permite medir la concordancia y calibrar umbrales con casos del
propio hospital. Las revisiones siguen siendo históricas (el trigger impide UPDATE/DELETE).
"""

from alembic import op


revision = '20261116_0018'
down_revision = '20261115_0017'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE public.imagen_revision_ia ADD COLUMN anormal_confirmado boolean')
    op.execute("COMMENT ON COLUMN public.imagen_revision_ia.anormal_confirmado IS "
               "'Lectura del médico al revisar la propuesta IA: true anormal, false normal, NULL no indicada. No es un diagnóstico publicado.'")


def downgrade():
    raise RuntimeError('No eliminar la lectura médica registrada automáticamente.')
