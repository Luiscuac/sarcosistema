"""Especialidad única histórica y creación idempotente de consultas."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '20261027_0007'
down_revision = '20261027_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    duplicado = bind.execute(sa.text('''
        SELECT medico_id, count(*) FROM public.medico_especialidad
        GROUP BY medico_id HAVING count(*) > 1 LIMIT 1
    ''')).first()
    if duplicado:
        raise RuntimeError(
            f'El médico {duplicado[0]} tiene {duplicado[1]} especialidades. '
            'Resuelve el conflicto manualmente antes de aplicar esta migración; no se borraron filas.'
        )

    op.add_column('medico_especialidad', sa.Column('vigente', sa.Boolean(), nullable=True), schema='public')
    bind.execute(sa.text('''
        UPDATE public.medico_especialidad
        SET vigente = (fecha_fin IS NULL OR fecha_fin >= CURRENT_DATE)
    '''))
    op.alter_column('medico_especialidad', 'vigente', nullable=False, schema='public')
    op.create_unique_constraint('uq_medico_especialidad_medico', 'medico_especialidad', ['medico_id'], schema='public')
    op.add_column('consulta', sa.Column('clave_idempotencia', UUID(as_uuid=True), nullable=True), schema='public')
    op.add_column('consulta', sa.Column('usuario_creacion_id', sa.BigInteger(), nullable=True), schema='public')
    op.create_foreign_key('fk_consulta_usuario_creacion', 'consulta', 'usuario', ['usuario_creacion_id'], ['id'], source_schema='public', referent_schema='public')
    op.create_unique_constraint('uq_consulta_usuario_clave', 'consulta', ['usuario_creacion_id', 'clave_idempotencia'], schema='public')


def downgrade() -> None:
    # No borrar trazabilidad, asignaciones ni consultas clínicas.
    pass
