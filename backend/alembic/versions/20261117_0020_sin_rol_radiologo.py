"""Elimina el rol `radiologo`: el rol `rayos_x` se encarga de todo el flujo de Rayos X.

Los usuarios que tuvieran el rol `radiologo` pasan a `rayos_x` (no se borra ningún usuario ni dato clínico).
En bases nuevas el rol ya no se crea (ver 20261116_0019), así que no hace nada.
"""
from alembic import op

revision = '20261117_0020'
down_revision = '20261116_0019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE public.usuario
           SET rol_id = (SELECT id FROM public.rol WHERE codigo = 'rayos_x')
         WHERE rol_id = (SELECT id FROM public.rol WHERE codigo = 'radiologo')
           AND EXISTS (SELECT 1 FROM public.rol WHERE codigo = 'rayos_x')
    """)
    op.execute("""
        DELETE FROM public.rol_permiso
         WHERE rol_id = (SELECT id FROM public.rol WHERE codigo = 'radiologo')
    """)
    op.execute("""
        DELETE FROM public.rol AS r
         WHERE r.codigo = 'radiologo'
           AND NOT EXISTS (SELECT 1 FROM public.usuario u WHERE u.rol_id = r.id)
    """)


def downgrade() -> None:
    # Los usuarios reasignados no se pueden distinguir de los que ya eran rayos_x: no se revierte.
    pass
