"""Catalogo de ecografias: el medico solicita, el radiologo sube imagenes e informe."""

from alembic import op


revision = "20261104_0012"
down_revision = "20261103_0011"
branch_labels = None
depends_on = None

ECOGRAFIAS = (
    ("ECO_ABDOMINAL", "Ecografia abdominal"),
    ("ECO_OBSTETRICA", "Ecografia obstetrica"),
    ("ECO_GINECOLOGICA", "Ecografia ginecologica"),
    ("ECO_RENAL", "Ecografia renal y vias urinarias"),
    ("ECO_PARTES_BLANDAS", "Ecografia de partes blandas"),
    ("ECO_TIROIDEA", "Ecografia tiroidea"),
    ("ECO_MAMARIA", "Ecografia mamaria"),
    ("ECO_DOPPLER", "Ecografia Doppler"),
)


def upgrade() -> None:
    op.execute("""
        INSERT INTO public.tipo_estudio
            (codigo, nombre, servicio_id, requiere_muestra, requiere_informe,
             requiere_archivos, activo)
        SELECT catalogo.codigo, catalogo.nombre, servicio.id,
               FALSE, TRUE, TRUE, TRUE
          FROM public.servicio AS servicio
         CROSS JOIN (VALUES
    """ + ",\n".join(f"            ('{codigo}', '{nombre}')" for codigo, nombre in ECOGRAFIAS) + """
         ) AS catalogo(codigo, nombre)
         WHERE servicio.codigo = 'IMG'
           AND NOT EXISTS (
               SELECT 1 FROM public.tipo_estudio existente
                WHERE existente.codigo = catalogo.codigo
                  AND existente.servicio_id = servicio.id
           )
    """)


def downgrade() -> None:
    codigos = ", ".join(f"'{codigo}'" for codigo, _ in ECOGRAFIAS)
    op.execute(f"""
        DELETE FROM public.tipo_estudio
         WHERE codigo IN ({codigos})
           AND servicio_id = (SELECT id FROM public.servicio WHERE codigo = 'IMG')
    """)
