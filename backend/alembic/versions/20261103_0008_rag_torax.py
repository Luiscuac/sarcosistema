"""Corpus documental experimental aislado de los registros clínicos."""
from alembic import op

revision = '20261103_0008'
down_revision = '20261104_0012'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('''CREATE TABLE public.rag_torax_documento (
        id text PRIMARY KEY,
        titulo text NOT NULL,
        fuente text NOT NULL,
        licencia text NOT NULL,
        categoria text NOT NULL,
        version text NOT NULL,
        sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
        contenido text NOT NULL CHECK (length(contenido)>0),
        creado_en timestamptz NOT NULL DEFAULT now()
    )''')
    op.execute('''CREATE TABLE public.rag_torax_fragmento (
        id text PRIMARY KEY,
        documento_id text NOT NULL REFERENCES public.rag_torax_documento(id),
        seccion text NOT NULL,
        inicio integer NOT NULL CHECK (inicio>=0),
        fin integer NOT NULL CHECK (fin>inicio),
        texto text NOT NULL CHECK (length(texto)=fin-inicio),
        modelo text NOT NULL,
        embedding vector(384) NOT NULL,
        UNIQUE(documento_id,inicio,fin,modelo)
    )''')
    # Corpus pequeño: búsqueda coseno exacta, sin índice ANN que omita vecinos.
    op.execute('CREATE INDEX ix_rag_torax_fragmento_documento ON public.rag_torax_fragmento(documento_id)')


def downgrade():
    raise RuntimeError('No borrar corpus ni extensión compartida automáticamente; requiere revisión manual.')
