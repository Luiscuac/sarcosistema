"""Cierra estudios con incidencia y los incorpora al informe final."""

from alembic import op


revision = "20261103_0011"
down_revision = "20261102_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_eeh_estado_nuevo", "estudio_estado_historial", schema="public")
    op.create_check_constraint(
        "ck_eeh_estado_nuevo",
        "estudio_estado_historial",
        "estado_nuevo IN ('pendiente_muestra','resultado_en_preparacion','publicado','invalidado','no_realizado')",
        schema="public",
    )
    op.drop_constraint("ck_estudio_estado", "estudio_solicitado", schema="public")
    op.create_check_constraint(
        "ck_estudio_estado",
        "estudio_solicitado",
        "estado IN ('pendiente_muestra','resultado_en_preparacion','publicado','invalidado','no_realizado')",
        schema="public",
    )
    op.execute("""
        UPDATE public.estudio_solicitado AS estudio
           SET estado = 'no_realizado',
               updated_at = now(),
               updated_by = ultima.usuario_id
          FROM (
              SELECT DISTINCT ON (estudio_id) estudio_id, usuario_id
                FROM public.incidencia_muestra
               ORDER BY estudio_id, fecha_hora DESC, id DESC
          ) AS ultima
         WHERE estudio.id = ultima.estudio_id
           AND estudio.estado = 'pendiente_muestra'
    """)
    op.execute("""
        CREATE OR REPLACE VIEW public.vista_solicitud_estado AS
        SELECT s.id AS solicitud_id,
               s.referencia,
               s.paciente_id,
               s.prioridad,
               s.fecha_solicitud,
               count(e.id) AS total_estudios,
               count(e.id) FILTER (WHERE e.estado = 'publicado') AS total_publicados,
               count(e.id) FILTER (WHERE e.estado = 'invalidado') AS total_invalidados,
               CASE
                   WHEN count(e.id) = 0 THEN 'sin_estudios'
                   WHEN count(e.id) FILTER (
                       WHERE e.estado IN ('publicado','invalidado','no_realizado')
                   ) = count(e.id) THEN 'completa'
                   WHEN count(e.id) FILTER (WHERE e.estado = 'publicado') > 0 THEN 'parcial'
                   ELSE 'pendiente'
               END AS estado_solicitud,
               array_agg(e.referencia) FILTER (WHERE e.estado = 'publicado') AS estudios_publicados,
               array_agg(e.referencia) FILTER (
                   WHERE e.estado IN ('pendiente_muestra','resultado_en_preparacion')
               ) AS estudios_pendientes
          FROM public.solicitud s
          LEFT JOIN public.estudio_solicitado e ON e.solicitud_id = s.id
         GROUP BY s.id
    """)


def downgrade() -> None:
    raise RuntimeError(
        "La migración 20261103_0011 registra cierres clínicos no realizados y no admite downgrade automático."
    )
