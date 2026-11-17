"""Radiologia convencional: catalogo configurable, adquisicion, imagenes por proyeccion e informe estructurado.

Cambio aditivo. No modifica ni elimina datos existentes:
- `tipo_estudio.configuracion_radiologia` (JSONB): region, lateralidad, proyecciones, protocolos y plantilla.
- Tablas `radiologia_*`: detalle de la solicitud por estudio, adquisicion tecnica, vinculo imagen-proyeccion,
  contenido estructurado del informe, adendas e informes externos.
- Siembra el catalogo inicial desde `app.imagenes.domain.catalogo_radiologia` sin tocar los nombres existentes.

`informe_imagen` y `archivo_imagen` no cambian: la asistencia IA sigue leyendo `descripcion_texto`,
`archivo_imagen.informe_id` y los hashes.
"""
import json

import sqlalchemy as sa
from alembic import op

from app.imagenes.domain.catalogo_radiologia import ESTUDIOS, configuracion_estudio


revision = '20261116_0019'
down_revision = '20261116_0018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('ALTER TABLE public.tipo_estudio ADD COLUMN IF NOT EXISTS configuracion_radiologia jsonb')
    op.execute("COMMENT ON COLUMN public.tipo_estudio.configuracion_radiologia IS "
               "'Configuracion editable del estudio radiologico: region, lateralidad, proyecciones, protocolos y plantilla de informe.'")

    op.execute("""
        CREATE TABLE public.radiologia_estudio_detalle (
            estudio_id bigint PRIMARY KEY REFERENCES public.estudio_solicitado(id),
            lateralidad text CHECK (lateralidad IN ('derecha','izquierda','bilateral')),
            protocolo_codigo text,
            proyecciones_solicitadas jsonb NOT NULL DEFAULT '[]'::jsonb,
            indicacion_clinica text,
            observaciones text,
            detalle_region text,
            motivo_no_realizado text,
            entregado_en timestamp with time zone,
            entregado_por bigint REFERENCES public.usuario(id),
            entregado_a text,
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            created_by bigint REFERENCES public.usuario(id)
        )
    """)
    op.execute("""
        CREATE TABLE public.radiologia_adquisicion (
            estudio_id bigint PRIMARY KEY REFERENCES public.estudio_solicitado(id),
            estado text NOT NULL DEFAULT 'en_proceso' CHECK (estado IN ('en_proceso','completada')),
            proyecciones_realizadas jsonb NOT NULL DEFAULT '[]'::jsonb,
            lateralidad_realizada text CHECK (lateralidad_realizada IN ('derecha','izquierda','bilateral')),
            posicion_paciente text,
            fecha_hora_adquisicion timestamp with time zone,
            operador_usuario_id bigint REFERENCES public.usuario(id),
            operador_nombre text,
            calidad text CHECK (calidad IN ('adecuada','limitada','no_diagnostica')),
            limitaciones text,
            repeticiones integer NOT NULL DEFAULT 0 CHECK (repeticiones >= 0),
            motivo_repeticion text,
            parametros jsonb NOT NULL DEFAULT '{}'::jsonb,
            observaciones text,
            completada_en timestamp with time zone,
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            updated_at timestamp with time zone NOT NULL DEFAULT now(),
            updated_by bigint REFERENCES public.usuario(id)
        )
    """)
    op.execute("""
        CREATE TABLE public.radiologia_imagen (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            estudio_id bigint NOT NULL REFERENCES public.estudio_solicitado(id),
            archivo_imagen_id bigint NOT NULL UNIQUE REFERENCES public.archivo_imagen(id),
            proyeccion_codigo text,
            created_at timestamp with time zone NOT NULL DEFAULT now()
        )
    """)
    op.execute('CREATE INDEX ix_radiologia_imagen_estudio ON public.radiologia_imagen (estudio_id)')
    op.execute("""
        CREATE TABLE public.radiologia_informe (
            informe_id bigint PRIMARY KEY REFERENCES public.informe_imagen(id),
            plantilla_codigo text NOT NULL,
            plantilla_version integer NOT NULL,
            contenido jsonb NOT NULL DEFAULT '{}'::jsonb,
            texto_personalizado boolean NOT NULL DEFAULT false,
            responsable_nombre text,
            registro_profesional text,
            version_edicion integer NOT NULL DEFAULT 1,
            updated_at timestamp with time zone NOT NULL DEFAULT now(),
            updated_by bigint REFERENCES public.usuario(id)
        )
    """)
    op.execute("""
        CREATE TABLE public.radiologia_adenda (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            informe_id bigint NOT NULL REFERENCES public.informe_imagen(id),
            motivo text NOT NULL CHECK (btrim(motivo) <> ''),
            texto text NOT NULL CHECK (btrim(texto) <> ''),
            usuario_id bigint NOT NULL REFERENCES public.usuario(id),
            autor_nombre text NOT NULL,
            registro_profesional text,
            fecha_hora timestamp with time zone NOT NULL DEFAULT now()
        )
    """)
    op.execute('CREATE INDEX ix_radiologia_adenda_informe ON public.radiologia_adenda (informe_id)')
    op.execute("""
        CREATE FUNCTION public.radiologia_adenda_inmutable() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'Las adendas son históricas: no se modifican ni eliminan'; END $$
    """)
    op.execute("""
        CREATE TRIGGER trg_radiologia_adenda_inmutable BEFORE UPDATE OR DELETE ON public.radiologia_adenda
        FOR EACH ROW EXECUTE FUNCTION public.radiologia_adenda_inmutable()
    """)
    op.execute("""
        CREATE TABLE public.radiologia_informe_externo (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            estudio_id bigint NOT NULL REFERENCES public.estudio_solicitado(id),
            nombre_original text NOT NULL,
            url_archivo text NOT NULL,
            mime_type text NOT NULL,
            tamano_bytes bigint NOT NULL,
            hash_sha256 text NOT NULL,
            establecimiento text NOT NULL CHECK (btrim(establecimiento) <> ''),
            profesional text,
            fecha_informe date,
            observaciones text,
            cargado_por bigint NOT NULL REFERENCES public.usuario(id),
            fecha_carga timestamp with time zone NOT NULL DEFAULT now(),
            activo boolean NOT NULL DEFAULT true,
            motivo_retiro text
        )
    """)
    op.execute('CREATE INDEX ix_radiologia_informe_externo_estudio ON public.radiologia_informe_externo (estudio_id)')

    # Un solo rol (rayos_x) se encarga del flujo completo: no se crea un rol de médico informante.

    conexion = op.get_bind()
    for estudio in ESTUDIOS:
        parametros = {'codigo': estudio.codigo, 'nombre': estudio.nombre,
                      'config': json.dumps(configuracion_estudio(estudio), ensure_ascii=False)}
        conexion.execute(sa.text("""
            INSERT INTO public.tipo_estudio (codigo, nombre, servicio_id, requiere_muestra, requiere_informe, requiere_archivos, activo)
            SELECT :codigo, :nombre, servicio.id, FALSE, TRUE, TRUE, TRUE
              FROM public.servicio AS servicio
             WHERE servicio.codigo = 'IMG'
               AND NOT EXISTS (SELECT 1 FROM public.tipo_estudio t WHERE t.codigo = :codigo AND t.servicio_id = servicio.id)
        """), parametros)
        conexion.execute(sa.text("""
            UPDATE public.tipo_estudio AS t SET configuracion_radiologia = CAST(:config AS jsonb)
              FROM public.servicio AS servicio
             WHERE servicio.id = t.servicio_id AND servicio.codigo = 'IMG' AND t.codigo = :codigo
               AND t.configuracion_radiologia IS NULL
        """), parametros)


def downgrade() -> None:
    raise RuntimeError('No eliminar automáticamente adquisiciones, informes estructurados ni adendas registradas.')
