"""Organiza prestaciones observadas en el registro mensual de laboratorio.

El archivo de origen contiene datos personales y no se importa. Solo se toman
encabezados de prestaciones. Las prestaciones sin plantilla pueden solicitarse,
pero no permiten capturar ni publicar resultados hasta definir su formato.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261026_0005"
down_revision = "20261022_0004"
branch_labels = None
depends_on = None


PRESTACIONES = (
    ("HEMOGRAMA_COMPLETO", "Hemograma completo", "hematologia"),
    ("HEMOGLOBINA_HEMATOCRITO", "Hemoglobina y hematocrito", "hematologia"),
    ("VES", "Velocidad de eritrosedimentación (VES)", "hematologia"),
    ("GRUPO_SANGUINEO", "Grupo sanguíneo y factor Rh", "hematologia"),
    ("QUIMICA_SANGUINEA", "Química sanguínea", "bioquimica"),
    ("GLICEMIA", "Glicemia", "bioquimica"),
    ("CREATININA_SERICA", "Creatinina sérica", "bioquimica"),
    ("UREA", "Urea", "bioquimica"),
    ("COLESTEROL_TOTAL", "Colesterol total", "bioquimica"),
    ("TRIGLICERIDOS", "Triglicéridos", "bioquimica"),
    ("PERFIL_LIPIDICO", "Perfil lipídico (HDL, LDL, VLDL)", "bioquimica"),
    ("ACIDO_URICO", "Ácido úrico", "bioquimica"),
    ("TRANSAMINASA_GOT", "Transaminasa GOT", "bioquimica"),
    ("TRANSAMINASA_GPT", "Transaminasa GPT", "bioquimica"),
    ("FOSFATASA_ALCALINA", "Fosfatasa alcalina", "bioquimica"),
    ("AMILASA", "Amilasa", "bioquimica"),
    ("BILIRRUBINAS", "Bilirrubinas", "bioquimica"),
    ("HEMOGLOBINA_GLICOSILADA", "Hemoglobina glicosilada", "bioquimica"),
    ("ELISA_CHAGAS", "ELISA para Chagas", "serologia"),
    ("ELISA_TOXOPLASMOSIS", "ELISA para toxoplasmosis", "serologia"),
    ("HAI_CHAGAS", "HAI para Chagas", "serologia"),
    ("VIH", "Prueba de VIH", "serologia"),
    ("RPR", "RPR", "serologia"),
    ("PSA", "PSA", "serologia"),
    ("HCG", "hCG", "serologia"),
    ("PCR_LATEX", "Proteína C reactiva por látex", "serologia"),
    ("FACTOR_REUMATOIDE", "Factor reumatoide", "serologia"),
    ("ASTO", "ASTO", "serologia"),
    ("REACCION_WIDAL", "Reacción de Widal", "serologia"),
    ("PRUEBA_RAPIDA_DENGUE", "Prueba rápida de dengue", "serologia"),
    ("EGO", "Examen general de orina", "copro_orina"),
    ("COPRO_SIMPLE", "Coproparasitológico simple", "copro_orina"),
    ("COPRO_SERIADO", "Coproparasitológico seriado", "copro_orina"),
    ("MOCO_FECAL", "Moco fecal", "copro_orina"),
    ("HELICOBACTER_HECES", "Helicobacter pylori en heces", "copro_orina"),
    ("SANGRE_OCULTA_HECES", "Sangre oculta en heces", "copro_orina"),
    ("ROTAVIRUS_HECES", "Rotavirus en heces", "copro_orina"),
)


def upgrade() -> None:
    op.add_column("paciente", sa.Column("historia_clinica", sa.Text(), nullable=True), schema="public")
    op.add_column("paciente", sa.Column("codigo_externo", sa.Text(), nullable=True), schema="public")
    op.add_column("tipo_estudio", sa.Column("categoria_laboratorio", sa.Text(), nullable=True), schema="public")
    op.create_check_constraint(
        "ck_tipo_estudio_categoria_laboratorio",
        "tipo_estudio",
        "categoria_laboratorio IS NULL OR categoria_laboratorio IN "
        "('hematologia', 'bioquimica', 'serologia', 'copro_orina')",
        schema="public",
    )

    bind = op.get_bind()
    servicio_id = bind.execute(
        sa.text("SELECT id FROM public.servicio WHERE codigo = 'LAB'")
    ).scalar_one()
    for codigo, nombre, categoria in PRESTACIONES:
        bind.execute(
            sa.text(
                """
                INSERT INTO public.tipo_estudio
                    (codigo, nombre, servicio_id, requiere_muestra,
                     requiere_informe, requiere_archivos, activo, categoria_laboratorio)
                VALUES (:codigo, :nombre, :servicio_id, TRUE, TRUE, FALSE, TRUE, :categoria)
                ON CONFLICT (codigo) DO UPDATE
                   SET categoria_laboratorio = EXCLUDED.categoria_laboratorio
                 WHERE public.tipo_estudio.servicio_id = EXCLUDED.servicio_id
                """
            ),
            {"codigo": codigo, "nombre": nombre, "servicio_id": servicio_id, "categoria": categoria},
        )


def downgrade() -> None:
    # Los identificadores pueden contener datos de pacientes y las prestaciones
    # pueden tener solicitudes asociadas. No se eliminan en un downgrade.
    pass
