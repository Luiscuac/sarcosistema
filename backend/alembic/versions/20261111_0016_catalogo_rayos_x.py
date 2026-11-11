"""Agrega radiografia de torax al catalogo de imagenes."""

from alembic import op


revision = '20261111_0016'
down_revision = ('20261109_0014', '20261110_0015')
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO public.rol (codigo, nombre, descripcion, activo)
        VALUES ('rayos_x', 'Personal de Rayos X', 'Rol para personal de radiografía', TRUE)
        ON CONFLICT (codigo) DO NOTHING
    """)
    op.execute("""
        INSERT INTO public.rol_permiso (rol_id, permiso_id)
        SELECT rol.id, permiso.id
          FROM public.rol AS rol
          CROSS JOIN public.permiso AS permiso
         WHERE rol.codigo = 'rayos_x'
           AND permiso.codigo IN ('crear','modificar','publicar','rectificar','invalidar','consultar','acceder')
        ON CONFLICT DO NOTHING
    """)
    op.execute("""
        INSERT INTO public.tipo_estudio
            (codigo, nombre, servicio_id, requiere_muestra, requiere_informe,
             requiere_archivos, activo)
        SELECT 'RX_TORAX', 'Radiografía de tórax', servicio.id,
               FALSE, TRUE, TRUE, TRUE
          FROM public.servicio AS servicio
         WHERE servicio.codigo = 'IMG'
           AND NOT EXISTS (
               SELECT 1 FROM public.tipo_estudio existente
                WHERE existente.codigo = 'RX_TORAX'
                  AND existente.servicio_id = servicio.id
           )
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM public.tipo_estudio
         WHERE codigo = 'RX_TORAX'
           AND servicio_id = (SELECT id FROM public.servicio WHERE codigo = 'IMG')
    """)
    op.execute("""
        DELETE FROM public.rol_permiso
         WHERE rol_id = (SELECT id FROM public.rol WHERE codigo = 'rayos_x')
    """)
    op.execute("""
        DELETE FROM public.rol
         WHERE codigo = 'rayos_x'
           AND NOT EXISTS (SELECT 1 FROM public.usuario WHERE rol_id = public.rol.id)
    """)
