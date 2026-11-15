"""Triaje visual automático (experimental) de radiografías al subirlas.

Una fila por archivo/estudio: ordena la bandeja de Rayos X. No es diagnóstico ni publica nada.
"""

from alembic import op


revision = '20261115_0017'
down_revision = '20261111_0016'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''CREATE TABLE public.imagen_triaje_ia (
        id uuid PRIMARY KEY,
        estudio_id bigint NOT NULL REFERENCES public.estudio_solicitado(id),
        archivo_id bigint NOT NULL REFERENCES public.archivo_imagen(id),
        archivo_sha256 text NOT NULL CHECK (archivo_sha256 ~ '^[0-9a-f]{64}$'),
        estado text NOT NULL DEFAULT 'en_cola' CHECK (estado IN ('en_cola','procesando','completado','error','interrumpido')),
        resultado jsonb,
        error_codigo text,
        creado_en timestamptz NOT NULL DEFAULT now(),
        actualizado_en timestamptz NOT NULL DEFAULT now(),
        UNIQUE (estudio_id, archivo_sha256)
    )''')
    op.execute("CREATE INDEX ix_imagen_triaje_ia_cola ON public.imagen_triaje_ia(creado_en, id) WHERE estado='en_cola'")
    op.execute('CREATE INDEX ix_imagen_triaje_ia_estudio ON public.imagen_triaje_ia(estudio_id)')


def downgrade():
    raise RuntimeError('No eliminar la trazabilidad del triaje automáticamente.')
