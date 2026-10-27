"""Agrega prestaciones iniciales leidas del formulario D-8.

Solo registra tipos de estudio. No carga resultados ni referencias clinicas;
las plantillas se configuraran luego de validarlas con el laboratorio.
"""

from alembic import op
import sqlalchemy as sa

revision = "20261022_0003"
down_revision = "20261022_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO public.tipo_estudio
                (codigo, nombre, servicio_id, requiere_muestra,
                 requiere_informe, requiere_archivos, activo)
            SELECT catalogo.codigo, catalogo.nombre, servicio.id,
                   TRUE, TRUE, FALSE, TRUE
              FROM public.servicio AS servicio
              CROSS JOIN (VALUES
                  ('HEMOGRAMA_COMPLETO', 'Hemograma completo'),
                  ('EGO', 'Examen general de orina'),
                  ('COPRO_SIMPLE', 'Coproparasitológico simple'),
                  ('COPRO_SERIADO', 'Coproparasitológico seriado')
              ) AS catalogo(codigo, nombre)
             WHERE servicio.codigo = 'LAB'
            ON CONFLICT (codigo) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    # No borrar prestaciones si ya tienen solicitudes asociadas.
    pass
