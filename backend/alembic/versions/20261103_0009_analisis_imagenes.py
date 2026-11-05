"""Análisis experimental y revisiones separados del informe clínico."""
from alembic import op

revision = '20261103_0009'
down_revision = '20261103_0008'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''CREATE TABLE public.imagen_analisis_ia (
        id uuid PRIMARY KEY,
        estudio_id bigint NOT NULL REFERENCES public.estudio_solicitado(id),
        informe_id bigint NOT NULL REFERENCES public.informe_imagen(id),
        archivo_id bigint NOT NULL REFERENCES public.archivo_imagen(id),
        solicitado_por bigint NOT NULL REFERENCES public.usuario(id),
        clave text NOT NULL CHECK (length(clave) BETWEEN 1 AND 100),
        proyeccion text NOT NULL CHECK (proyeccion IN ('PA','AP','frontal_no_especificada')),
        informe_texto text NOT NULL,
        informe_sha256 text NOT NULL CHECK (informe_sha256 ~ '^[0-9a-f]{64}$'),
        archivo_sha256 text NOT NULL CHECK (archivo_sha256 ~ '^[0-9a-f]{64}$'),
        estado text NOT NULL DEFAULT 'en_cola' CHECK (estado IN ('en_cola','procesando','completado','error','interrumpido')),
        resultado jsonb,
        error_codigo text,
        version_revision integer NOT NULL DEFAULT 0 CHECK (version_revision>=0),
        creado_en timestamptz NOT NULL DEFAULT now(),
        actualizado_en timestamptz NOT NULL DEFAULT now(),
        UNIQUE(solicitado_por,clave)
    )''')
    op.execute("CREATE UNIQUE INDEX uq_imagen_ia_trabajo_activo ON public.imagen_analisis_ia(estudio_id) WHERE estado IN ('en_cola','procesando')")
    op.execute('''CREATE TABLE public.imagen_revision_ia (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        analisis_id uuid NOT NULL REFERENCES public.imagen_analisis_ia(id),
        usuario_id bigint NOT NULL REFERENCES public.usuario(id),
        version integer NOT NULL CHECK (version>0),
        decision text NOT NULL CHECK (decision IN ('aceptada_como_propuesta','corregida','rechazada')),
        motivo text NOT NULL,
        correccion text,
        fecha timestamptz NOT NULL DEFAULT now(),
        UNIQUE(analisis_id,version),
        CHECK (decision='aceptada_como_propuesta' OR length(trim(motivo))>0),
        CHECK (decision<>'corregida' OR length(trim(correccion))>0)
    )''')
    op.execute('''CREATE FUNCTION public.proteger_revision_ia() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'La revisión experimental es histórica y no se modifica ni elimina'; END $$''')
    op.execute('CREATE TRIGGER trg_revision_ia_historica BEFORE UPDATE OR DELETE ON public.imagen_revision_ia FOR EACH ROW EXECUTE FUNCTION public.proteger_revision_ia()')


def downgrade():
    raise RuntimeError('No eliminar trazabilidad de análisis/revisión automáticamente.')
