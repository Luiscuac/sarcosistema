"""Carga los formatos iniciales de laboratorio transcritos por el equipo.

Los rangos se conservan como texto, tal como se leyeron del D-9. No se
configuran validaciones numéricas automáticas ni opciones cualitativas no
confirmadas. El campo ilegible de orina queda excluido.
"""

from alembic import op
import sqlalchemy as sa

revision = "20261022_0004"
down_revision = "20261022_0003"
branch_labels = None
depends_on = None


FORMATOS = (
    {
        "codigo": "FORM_HEMOGRAMA_COMPLETO",
        "nombre": "Hemograma completo",
        "secciones": (("Hemograma", 1),),
        "tipos": ("HEMOGRAMA_COMPLETO",),
        "parametros": (
            ("gr", "Glóbulos rojos (GR)", "decimal", "mm³", None, 1, 1, True),
            ("gb", "Glóbulos blancos (GB)", "decimal", "mm³", None, 2, 1, True),
            ("hto", "Hematocrito (Hto.)", "decimal", "%", None, 3, 1, True),
            ("hb", "Hemoglobina (Hb)", "decimal", "g/dL", None, 4, 1, True),
            ("plaquetas", "Plaquetas", "decimal", "mm³", None, 5, 1, True),
            ("seg", "Segmentados (SEG)", "decimal", "%", None, 6, 1, True),
            ("lin", "Linfocitos (LIN)", "decimal", "%", None, 7, 1, True),
            ("eos", "Eosinófilos (EOS)", "decimal", "%", None, 8, 1, True),
            ("bas", "Basófilos (BAS)", "decimal", "%", None, 9, 1, True),
            ("mon", "Monocitos (MON)", "decimal", "%", None, 10, 1, True),
            ("cay", "Cayados (CAY)", "decimal", "%", None, 11, 1, True),
        ),
    },
    {
        "codigo": "FORM_EGO",
        "nombre": "Examen general de orina",
        "secciones": (("Examen físico y químico", 1), ("Examen microscópico", 2)),
        "tipos": ("EGO",),
        "parametros": (
            ("color", "Color", "texto", None, None, 1, 1, True),
            ("olor", "Olor", "texto", None, None, 2, 1, True),
            ("aspecto", "Aspecto", "texto", None, None, 3, 1, True),
            ("densidad", "Densidad", "texto", None, None, 4, 1, True),
            ("ph", "pH", "decimal", None, None, 5, 1, True),
            ("proteinas", "Proteínas", "texto", None, None, 6, 1, True),
            ("hemoglobina", "Hemoglobina", "texto", None, None, 7, 1, True),
            ("glucosa", "Glucosa", "texto", None, None, 8, 1, True),
            ("cetonas", "Cetonas", "texto", None, None, 9, 1, True),
            ("urobilina", "Urobilina", "texto", None, None, 10, 1, True),
            ("nitritos", "Nitritos", "texto", None, None, 11, 1, True),
            ("leucocitos_quimico", "Leucocitos", "texto", None, None, 12, 1, True),
            ("bilirrubina", "Bilirrubina", "texto", None, None, 13, 1, True),
            ("celulas_epiteliales", "Células epiteliales", "texto", None, None, 14, 2, True),
            ("celulas_transicion", "Células de transición", "texto", None, None, 15, 2, True),
            ("celulas_redondas", "Células redondas", "texto", None, None, 16, 2, True),
            ("leucocitos_microscopico", "Leucocitos", "texto", None, None, 17, 2, True),
            ("eritrocitos", "Eritrocitos", "texto", None, None, 18, 2, True),
            ("flora_bacteriana", "Flora bacteriana", "texto", None, None, 19, 2, True),
            ("filamentos_mucoides", "Filamentos mucoides", "texto", None, None, 20, 2, True),
            ("trichomonas_vaginalis", "Trichomonas vaginalis", "texto", None, None, 21, 2, True),
            ("cilindros_granulosos", "Cilindros granulosos", "texto", None, None, 22, 2, True),
            ("cilindros_hialinos", "Cilindros hialinos", "texto", None, None, 23, 2, True),
            ("cristales", "Cristales", "texto", None, None, 24, 2, True),
        ),
    },
    {
        "codigo": "FORM_COPROPARASITOLOGIA",
        "nombre": "Coproparasitología",
        "secciones": (("Examen macroscópico", 1), ("Examen microscópico", 2)),
        "tipos": ("COPRO_SIMPLE", "COPRO_SERIADO"),
        "parametros": (
            ("color", "Color", "texto", None, None, 1, 1, True),
            ("consistencia", "Consistencia", "texto", None, None, 2, 1, True),
            ("restos_alimenticios", "Restos alimenticios", "texto", None, None, 3, 1, True),
            ("otros_macro", "Otros", "texto", None, None, 4, 1, False),
            ("hallazgo_parasitologico", "Hallazgo parasitológico", "texto", None, None, 5, 2, True),
            ("flora_bacteriana", "Flora bacteriana", "texto", None, None, 6, 2, True),
            ("leucocitos", "Leucocitos", "texto", None, None, 7, 2, True),
            ("eritrocitos", "Eritrocitos", "texto", None, None, 8, 2, True),
        ),
    },
    {
        "codigo": "FORM_QUIMICA_SANGUINEA",
        "nombre": "Química sanguínea",
        "secciones": (("Resultados", 1),),
        "tipos": ("QUIMICA_SANGUINEA",),
        "parametros": (
            ("acido_urico", "Ácido úrico", "decimal", "mg/dL", "2.4–7.0 mg/dL", 1, 1, True),
            ("glicemia", "Glicemia", "decimal", "mg/dL", "70–115 mg/dL", 2, 1, True),
            ("creatinina", "Creatinina sérica", "decimal", "mg/dL", "0.6–1.3 mg/dL", 3, 1, True),
            ("colesterol_total", "Colesterol total", "decimal", "mg/dL", "Menor a 190 mg/dL", 4, 1, True),
            ("hdl_colesterol", "HDL-colesterol", "decimal", "mg/dL", "Mayor a 45 mg/dL", 5, 1, True),
            ("ldl_colesterol", "LDL-colesterol", "decimal", "mg/dL", "Menor a 190 mg/dL", 6, 1, True),
            ("trigliceridos", "Triglicéridos", "decimal", "mg/dL", "Hasta 200 mg/dL", 7, 1, True),
            ("urea", "Urea", "decimal", "mg/dL", "10–50 mg/dL", 8, 1, True),
            ("bun", "BUN (nitrógeno ureico)", "decimal", "mg/dL", "10–20 mg/dL", 9, 1, True),
            ("transaminasa_got", "Transaminasa GOT", "decimal", "U/L", "Hasta 37 U/L", 10, 1, True),
            ("transaminasa_gpt", "Transaminasa GPT", "decimal", "U/L", "Hasta 42 U/L", 11, 1, True),
            ("bilirrubina_directa", "Bilirrubina directa (B.D.)", "decimal", "mg/dL", "Hasta 0.2 mg/dL", 12, 1, True),
            ("bilirrubina_indirecta", "Bilirrubina indirecta (B.I.)", "decimal", "mg/dL", "Hasta 0.8 mg/dL", 13, 1, True),
            ("bilirrubina_total", "Bilirrubina total", "decimal", "mg/dL", "Hasta 1.0 mg/dL", 14, 1, True),
        ),
    },
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO public.tipo_estudio
                (codigo, nombre, servicio_id, requiere_muestra,
                 requiere_informe, requiere_archivos, activo)
            SELECT 'QUIMICA_SANGUINEA', 'Química sanguínea', id,
                   TRUE, TRUE, FALSE, TRUE
              FROM public.servicio
             WHERE codigo = 'LAB'
            ON CONFLICT (codigo) DO NOTHING
            """
        )
    )

    servicio_id = bind.execute(
        sa.text("SELECT id FROM public.servicio WHERE codigo = 'LAB'")
    ).scalar_one()

    for formato in FORMATOS:
        bind.execute(
            sa.text(
                """
                INSERT INTO public.plantilla_examen (codigo, nombre, servicio_id, activo)
                VALUES (:codigo, :nombre, :servicio_id, TRUE)
                ON CONFLICT (codigo) DO UPDATE
                    SET nombre = EXCLUDED.nombre, servicio_id = EXCLUDED.servicio_id,
                        activo = TRUE
                """
            ),
            {"codigo": formato["codigo"], "nombre": formato["nombre"], "servicio_id": servicio_id},
        )
        plantilla_id = bind.execute(
            sa.text("SELECT id FROM public.plantilla_examen WHERE codigo = :codigo"),
            {"codigo": formato["codigo"]},
        ).scalar_one()

        bind.execute(
            sa.text(
                """
                INSERT INTO public.plantilla_examen_version
                    (plantilla_examen_id, numero_version, estado, fecha_activacion,
                     usuario_activacion_id, created_at, updated_at)
                VALUES (:plantilla_id, 1, 'activa', now(), NULL, now(), now())
                ON CONFLICT (plantilla_examen_id, numero_version) DO UPDATE
                    SET estado = 'activa', fecha_activacion = COALESCE(
                        public.plantilla_examen_version.fecha_activacion, now()
                    ), updated_at = now()
                """
            ),
            {"plantilla_id": plantilla_id},
        )
        version_id = bind.execute(
            sa.text(
                """SELECT id FROM public.plantilla_examen_version
                    WHERE plantilla_examen_id = :plantilla_id AND numero_version = 1"""
            ),
            {"plantilla_id": plantilla_id},
        ).scalar_one()

        section_ids = {}
        for section_name, section_order in formato["secciones"]:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO public.seccion_plantilla
                        (plantilla_version_id, nombre, orden)
                    VALUES (:version_id, :nombre, :orden)
                    ON CONFLICT (plantilla_version_id, orden) DO UPDATE
                        SET nombre = EXCLUDED.nombre, updated_at = now()
                    """
                ),
                {"version_id": version_id, "nombre": section_name, "orden": section_order},
            )
            section_ids[section_order] = bind.execute(
                sa.text(
                    """SELECT id FROM public.seccion_plantilla
                        WHERE plantilla_version_id = :version_id AND orden = :orden"""
                ),
                {"version_id": version_id, "orden": section_order},
            ).scalar_one()

        for (code, name, input_type, unit, reference, order, section_order, required) in formato["parametros"]:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO public.parametro_plantilla
                        (plantilla_version_id, seccion_id, nombre, codigo, tipo_entrada,
                         unidad, rango_referencia_texto, valor_minimo, valor_maximo,
                         obligatorio, orden, precision_decimal)
                    VALUES (:version_id, :section_id, :name, :code, :input_type,
                            :unit, :reference, NULL, NULL, :required, :ordering, NULL)
                    ON CONFLICT (plantilla_version_id, codigo) DO UPDATE
                        SET seccion_id = EXCLUDED.seccion_id,
                            nombre = EXCLUDED.nombre,
                            tipo_entrada = EXCLUDED.tipo_entrada,
                            unidad = EXCLUDED.unidad,
                            rango_referencia_texto = EXCLUDED.rango_referencia_texto,
                            obligatorio = EXCLUDED.obligatorio,
                            orden = EXCLUDED.orden
                    """
                ),
                {
                    "version_id": version_id,
                    "section_id": section_ids[section_order],
                    "name": name,
                    "code": code,
                    "input_type": input_type,
                    "unit": unit,
                    "reference": reference,
                    "required": required,
                    "ordering": order,
                },
            )

        for type_code in formato["tipos"]:
            bind.execute(
                sa.text(
                    """UPDATE public.tipo_estudio SET plantilla_examen_id = :plantilla_id
                        WHERE codigo = :type_code AND servicio_id = :servicio_id"""
                ),
                {"plantilla_id": plantilla_id, "type_code": type_code, "servicio_id": servicio_id},
            )


def downgrade() -> None:
    # Se conservan los formatos y resultados asociados para no invalidar
    # capturas realizadas después de aplicar esta revisión.
    pass
