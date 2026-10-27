"""Habilita una captura libre versionada para prestaciones sin formato propio.

Cada estudio recibe su propia plantilla v1 con resultado y unidad opcional.
Las plantillas clínicas existentes no se modifican. Cuando el hospital entregue
sus parámetros, se activará una versión nueva por prestación.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261027_0006"
down_revision = "20261026_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    estudios = bind.execute(sa.text("""
        SELECT t.id, t.codigo, t.nombre, t.servicio_id
          FROM public.tipo_estudio AS t
          JOIN public.servicio AS s ON s.id = t.servicio_id
         WHERE s.codigo = 'LAB'
           AND t.categoria_laboratorio IS NOT NULL
           AND t.plantilla_examen_id IS NULL
         ORDER BY t.id
    """)).mappings().all()

    for estudio in estudios:
        codigo_plantilla = f"FORM_LIBRE_{estudio['codigo']}"
        bind.execute(sa.text("""
            INSERT INTO public.plantilla_examen (codigo, nombre, servicio_id, activo)
            VALUES (:codigo, :nombre, :servicio_id, TRUE)
            ON CONFLICT (codigo) DO NOTHING
        """), {
            "codigo": codigo_plantilla,
            "nombre": estudio["nombre"],
            "servicio_id": estudio["servicio_id"],
        })
        plantilla_id = bind.execute(sa.text("""
            SELECT id FROM public.plantilla_examen WHERE codigo = :codigo
        """), {"codigo": codigo_plantilla}).scalar_one()
        bind.execute(sa.text("""
            INSERT INTO public.plantilla_examen_version
                (plantilla_examen_id, numero_version, estado, fecha_activacion,
                 usuario_activacion_id, created_at, updated_at)
            VALUES (:plantilla_id, 1, 'activa', now(), NULL, now(), now())
            ON CONFLICT (plantilla_examen_id, numero_version) DO NOTHING
        """), {"plantilla_id": plantilla_id})
        version_id = bind.execute(sa.text("""
            SELECT id FROM public.plantilla_examen_version
             WHERE plantilla_examen_id = :plantilla_id AND numero_version = 1
        """), {"plantilla_id": plantilla_id}).scalar_one()
        bind.execute(sa.text("""
            INSERT INTO public.seccion_plantilla (plantilla_version_id, nombre, orden)
            VALUES (:version_id, 'Resultado', 1)
            ON CONFLICT (plantilla_version_id, orden) DO NOTHING
        """), {"version_id": version_id})
        seccion_id = bind.execute(sa.text("""
            SELECT id FROM public.seccion_plantilla
             WHERE plantilla_version_id = :version_id AND orden = 1
        """), {"version_id": version_id}).scalar_one()
        for codigo, nombre, obligatorio, orden in (
            ("resultado", "Resultado", True, 1),
            ("unidad_reportada", "Unidad (si aplica)", False, 2),
        ):
            bind.execute(sa.text("""
                INSERT INTO public.parametro_plantilla
                    (plantilla_version_id, seccion_id, nombre, codigo, tipo_entrada,
                     unidad, rango_referencia_texto, valor_minimo, valor_maximo,
                     obligatorio, orden, precision_decimal)
                VALUES (:version_id, :seccion_id, :nombre, :codigo, 'texto',
                        NULL, NULL, NULL, NULL, :obligatorio, :orden, NULL)
                ON CONFLICT (plantilla_version_id, codigo) DO NOTHING
            """), {
                "version_id": version_id,
                "seccion_id": seccion_id,
                "nombre": nombre,
                "codigo": codigo,
                "obligatorio": obligatorio,
                "orden": orden,
            })
        bind.execute(sa.text("""
            UPDATE public.tipo_estudio
               SET plantilla_examen_id = :plantilla_id
             WHERE id = :estudio_id AND plantilla_examen_id IS NULL
        """), {"plantilla_id": plantilla_id, "estudio_id": estudio["id"]})


def downgrade() -> None:
    # Se preservan plantillas y resultados que puedan haberse capturado.
    pass
