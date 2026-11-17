"""Conserva los datos manuales de las plantillas de ecografía por versión."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20261114_0017'
down_revision = '20261111_0016'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('informe_imagen', sa.Column('datos_ecografia', postgresql.JSONB(), nullable=True), schema='public')
    op.create_check_constraint('ck_informe_ecografia_objeto', 'informe_imagen',
                               "datos_ecografia IS NULL OR jsonb_typeof(datos_ecografia) = 'object'", schema='public')


def downgrade():
    raise RuntimeError('No se eliminan los datos históricos de los informes de ecografía.')
