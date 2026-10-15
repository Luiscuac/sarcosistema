-- =====================================================================
-- HOSPITAL SARCOBAMBA - ESQUEMA COMPLETO Y CORREGIDO
-- Generado el 2026-09-24 combinando:
--   1) El script original de database.build (tablas, PK, FK base)
--   2) El complemento: tablas faltantes, checks, indices, triggers,
--      vistas y datos semilla que el original no incluia
-- Ejecutable de una sola vez, de principio a fin, en PGlite/PostgreSQL.
-- =====================================================================

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3 (PGlite 0.2.0)
-- Dumped by pg_dump version 16.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'SQL_ASCII';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET escape_string_warning = off;
SET row_security = off;

--
-- Name: actualizar_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.actualizar_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;



SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: archivo_imagen; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archivo_imagen (
    id bigint NOT NULL,
    informe_id bigint NOT NULL,
    nombre_original text NOT NULL,
    url_archivo text NOT NULL,
    mime_type text NOT NULL,
    tamano_bytes bigint NOT NULL,
    hash_sha256 text NOT NULL,
    fecha_carga timestamp with time zone NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    motivo_retiro text,
    archivo_reemplazado_id bigint,
    created_by bigint NOT NULL
);



--
-- Name: archivo_imagen_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.archivo_imagen ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.archivo_imagen_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: asignacion_horario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.asignacion_horario (
    id bigint NOT NULL,
    trabajador_id bigint NOT NULL,
    horario_id bigint NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date
);



--
-- Name: asignacion_horario_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.asignacion_horario ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.asignacion_horario_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auditoria_accion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auditoria_accion (
    id bigint NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    usuario_id bigint NOT NULL,
    accion text NOT NULL,
    entidad_afectada text NOT NULL,
    referencia_registro text,
    detalle jsonb,
    created_at timestamp with time zone DEFAULT now()
);



--
-- Name: auditoria_accion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auditoria_accion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.auditoria_accion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: consulta; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.consulta (
    id bigint NOT NULL,
    paciente_id bigint NOT NULL,
    medico_id bigint NOT NULL,
    especialidad_id bigint NOT NULL,
    turno_id bigint,
    fecha_hora_inicio timestamp with time zone NOT NULL,
    fecha_hora_fin timestamp with time zone,
    motivo_consulta text NOT NULL,
    estado text NOT NULL,
    datos_clinicos_jsonb jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);



--
-- Name: consulta_audio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.consulta_audio (
    id bigint NOT NULL,
    consulta_id bigint NOT NULL,
    archivo_url text NOT NULL,
    mime_type text NOT NULL,
    duracion interval,
    hash_sha256 text NOT NULL,
    fecha_carga timestamp with time zone NOT NULL,
    usuario_id bigint NOT NULL
);



--
-- Name: consulta_audio_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.consulta_audio ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.consulta_audio_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: consulta_diagnostico; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.consulta_diagnostico (
    consulta_id bigint NOT NULL,
    diagnostico_id bigint NOT NULL,
    principal boolean DEFAULT false NOT NULL
);



--
-- Name: consulta_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.consulta ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.consulta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: correccion_paciente_consulta; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.correccion_paciente_consulta (
    id bigint NOT NULL,
    consulta_id bigint NOT NULL,
    paciente_anterior_id bigint NOT NULL,
    paciente_nuevo_id bigint NOT NULL,
    motivo text NOT NULL,
    usuario_responsable_id bigint NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    CONSTRAINT correccion_paciente_consulta_check CHECK ((paciente_anterior_id <> paciente_nuevo_id))
);



--
-- Name: correccion_paciente_consulta_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.correccion_paciente_consulta ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.correccion_paciente_consulta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: correccion_paciente_estudio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.correccion_paciente_estudio (
    id bigint NOT NULL,
    estudio_id bigint NOT NULL,
    paciente_anterior_id bigint NOT NULL,
    paciente_nuevo_id bigint NOT NULL,
    motivo text NOT NULL,
    usuario_responsable_id bigint NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    CONSTRAINT correccion_paciente_estudio_check CHECK ((paciente_anterior_id <> paciente_nuevo_id))
);



--
-- Name: correccion_paciente_estudio_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.correccion_paciente_estudio ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.correccion_paciente_estudio_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: correccion_paciente_muestra; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.correccion_paciente_muestra (
    id bigint NOT NULL,
    muestra_id bigint NOT NULL,
    paciente_anterior_id bigint NOT NULL,
    paciente_nuevo_id bigint NOT NULL,
    motivo text NOT NULL,
    usuario_responsable_id bigint NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    CONSTRAINT correccion_paciente_muestra_check CHECK ((paciente_anterior_id <> paciente_nuevo_id))
);



--
-- Name: correccion_paciente_muestra_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.correccion_paciente_muestra ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.correccion_paciente_muestra_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: correccion_paciente_receta; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.correccion_paciente_receta (
    id bigint NOT NULL,
    receta_id bigint NOT NULL,
    paciente_anterior_id bigint NOT NULL,
    paciente_nuevo_id bigint NOT NULL,
    motivo text NOT NULL,
    usuario_responsable_id bigint NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    CONSTRAINT correccion_paciente_receta_check CHECK ((paciente_anterior_id <> paciente_nuevo_id))
);



--
-- Name: correccion_paciente_receta_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.correccion_paciente_receta ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.correccion_paciente_receta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: correccion_paciente_solicitud; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.correccion_paciente_solicitud (
    id bigint NOT NULL,
    solicitud_id bigint NOT NULL,
    paciente_anterior_id bigint NOT NULL,
    paciente_nuevo_id bigint NOT NULL,
    motivo text NOT NULL,
    usuario_responsable_id bigint NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    CONSTRAINT correccion_paciente_solicitud_check CHECK ((paciente_anterior_id <> paciente_nuevo_id))
);



--
-- Name: correccion_paciente_solicitud_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.correccion_paciente_solicitud ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.correccion_paciente_solicitud_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: detalle_valor_resultado; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detalle_valor_resultado (
    id bigint NOT NULL,
    version_resultado_id bigint NOT NULL,
    parametro_id bigint NOT NULL,
    valor_entero integer,
    valor_decimal numeric,
    valor_texto text,
    valor_cualitativo text,
    fuera_de_rango boolean DEFAULT false NOT NULL
);



--
-- Name: detalle_valor_resultado_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.detalle_valor_resultado ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.detalle_valor_resultado_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: diagnostico_cie10; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.diagnostico_cie10 (
    id bigint NOT NULL,
    codigo text NOT NULL,
    descripcion text NOT NULL,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: diagnostico_cie10_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.diagnostico_cie10 ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.diagnostico_cie10_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: especialidad; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.especialidad (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: especialidad_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.especialidad ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.especialidad_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: establecimiento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.establecimiento (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    tipo text NOT NULL,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: establecimiento_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.establecimiento ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.establecimiento_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estadistica_indicador; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estadistica_indicador (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    descripcion text
);



--
-- Name: estadistica_indicador_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.estadistica_indicador ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.estadistica_indicador_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estadistica_regla_correspondencia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estadistica_regla_correspondencia (
    id bigint NOT NULL,
    indicador_id bigint NOT NULL,
    campo_origen text NOT NULL,
    version integer NOT NULL
);



--
-- Name: estadistica_regla_correspondencia_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.estadistica_regla_correspondencia ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.estadistica_regla_correspondencia_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estadistica_reporte; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estadistica_reporte (
    id bigint NOT NULL,
    nombre text NOT NULL,
    descripcion text
);



--
-- Name: estadistica_reporte_fuente; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estadistica_reporte_fuente (
    id bigint NOT NULL,
    reporte_version_id bigint NOT NULL,
    fuente_datos text NOT NULL
);



--
-- Name: estadistica_reporte_fuente_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.estadistica_reporte_fuente ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.estadistica_reporte_fuente_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estadistica_reporte_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.estadistica_reporte ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.estadistica_reporte_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estadistica_reporte_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estadistica_reporte_version (
    id bigint NOT NULL,
    reporte_id bigint NOT NULL,
    numero_version integer NOT NULL,
    periodo_inicio date NOT NULL,
    periodo_fin date NOT NULL,
    contenido_jsonb jsonb,
    origen_exportacion text,
    usuario_confirmacion_id bigint,
    fecha_generacion timestamp with time zone,
    estado text NOT NULL
);



--
-- Name: estadistica_reporte_version_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.estadistica_reporte_version ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.estadistica_reporte_version_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estudio_solicitado; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estudio_solicitado (
    id bigint NOT NULL,
    referencia text NOT NULL,
    solicitud_id bigint NOT NULL,
    paciente_id bigint NOT NULL,
    servicio_id bigint NOT NULL,
    tipo_estudio_id bigint NOT NULL,
    estado text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);



--
-- Name: estudio_solicitado_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.estudio_solicitado ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.estudio_solicitado_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: evento_atencion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.evento_atencion (
    id bigint NOT NULL,
    turno_id bigint,
    consulta_id bigint,
    tipo_evento text NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    usuario_id bigint NOT NULL,
    detalle text
);



--
-- Name: evento_atencion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.evento_atencion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.evento_atencion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: farmacia_entrega; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.farmacia_entrega (
    id bigint NOT NULL,
    receta_version_id bigint NOT NULL,
    entregado_por_usuario_id bigint NOT NULL,
    tipo_entrega text NOT NULL,
    recibido_por text NOT NULL,
    tipo_receptor text NOT NULL,
    identificacion_receptor text,
    referencia_comprobante text,
    fecha_hora timestamp with time zone NOT NULL,
    clave_idempotencia text
);



--
-- Name: farmacia_entrega_detalle; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.farmacia_entrega_detalle (
    id bigint NOT NULL,
    entrega_id bigint NOT NULL,
    receta_detalle_id bigint NOT NULL,
    cantidad_entregada numeric NOT NULL,
    unidad text NOT NULL
);



--
-- Name: farmacia_entrega_detalle_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.farmacia_entrega_detalle ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.farmacia_entrega_detalle_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: farmacia_entrega_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.farmacia_entrega ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.farmacia_entrega_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: farmacia_receta; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.farmacia_receta (
    id bigint NOT NULL,
    paciente_id bigint NOT NULL,
    medico_id bigint NOT NULL,
    fecha_emision timestamp with time zone NOT NULL,
    estado text NOT NULL,
    establecimiento_id bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);



--
-- Name: farmacia_receta_detalle; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.farmacia_receta_detalle (
    id bigint NOT NULL,
    receta_version_id bigint NOT NULL,
    medicamento_id bigint NOT NULL,
    nombre_medicamento_snapshot text NOT NULL,
    presentacion_snapshot text,
    concentracion_snapshot text,
    cantidad_prescrita numeric NOT NULL,
    unidad text NOT NULL,
    dosis text,
    frecuencia text,
    duracion text,
    via_administracion text,
    indicaciones text
);



--
-- Name: farmacia_receta_detalle_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.farmacia_receta_detalle ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.farmacia_receta_detalle_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: farmacia_receta_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.farmacia_receta ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.farmacia_receta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: farmacia_receta_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.farmacia_receta_version (
    id bigint NOT NULL,
    receta_id bigint NOT NULL,
    numero_version integer NOT NULL,
    estado text NOT NULL,
    motivo_cambio text,
    usuario_emision_id bigint,
    fecha_emision timestamp with time zone
);



--
-- Name: farmacia_receta_version_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.farmacia_receta_version ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.farmacia_receta_version_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: horario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.horario (
    id bigint NOT NULL,
    nombre text NOT NULL,
    descripcion text
);



--
-- Name: horario_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.horario ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.horario_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: horario_jornada; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.horario_jornada (
    id bigint NOT NULL,
    horario_id bigint NOT NULL,
    dia_semana text NOT NULL,
    hora_inicio time without time zone NOT NULL,
    hora_fin time without time zone NOT NULL,
    turno text,
    jornada_aplicable text
);



--
-- Name: horario_jornada_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.horario_jornada ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.horario_jornada_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ia_fuente; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ia_fuente (
    id bigint NOT NULL,
    generacion_id bigint NOT NULL,
    tipo_fuente text NOT NULL,
    referencia text NOT NULL,
    fragmento text,
    fecha_version timestamp with time zone
);



--
-- Name: ia_fuente_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.ia_fuente ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ia_fuente_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ia_generacion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ia_generacion (
    id bigint NOT NULL,
    paciente_id bigint NOT NULL,
    consulta_id bigint NOT NULL,
    tipo_generacion text NOT NULL,
    modelo text NOT NULL,
    version_modelo text NOT NULL,
    contenido_generado text NOT NULL,
    estado_revision text NOT NULL,
    usuario_revisor_id bigint,
    fecha_generacion timestamp with time zone NOT NULL,
    fecha_revision timestamp with time zone
);



--
-- Name: ia_generacion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.ia_generacion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ia_generacion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: importacion_archivo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.importacion_archivo (
    id bigint NOT NULL,
    tipo_importacion text NOT NULL,
    nombre_archivo text NOT NULL,
    hash_sha256 text NOT NULL,
    fecha_hora_carga timestamp with time zone NOT NULL,
    usuario_id bigint NOT NULL,
    periodo_inicio date,
    periodo_fin date,
    estado text NOT NULL,
    total_registros integer,
    total_validos integer,
    total_rechazados integer,
    datos_resumen_json jsonb
);



--
-- Name: importacion_archivo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.importacion_archivo ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.importacion_archivo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: importacion_detalle; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.importacion_detalle (
    id bigint NOT NULL,
    importacion_id bigint NOT NULL,
    numero_fila integer NOT NULL,
    clave_origen text,
    datos_json jsonb,
    estado text NOT NULL,
    motivo_error text
);



--
-- Name: importacion_detalle_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.importacion_detalle ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.importacion_detalle_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: informe_imagen; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.informe_imagen (
    id bigint NOT NULL,
    estudio_id bigint NOT NULL,
    numero_version integer NOT NULL,
    descripcion_texto text,
    estado text NOT NULL,
    motivo_rectificacion text,
    usuario_publicacion_id bigint,
    fecha_hora_publicacion timestamp with time zone,
    version_anterior_id bigint,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);



--
-- Name: informe_imagen_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.informe_imagen ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.informe_imagen_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: medicamento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medicamento (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    principio_activo text,
    presentacion text,
    concentracion text,
    unidad text,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: medicamento_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.medicamento ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.medicamento_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: medico; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medico (
    id bigint NOT NULL,
    trabajador_id bigint NOT NULL,
    matricula_profesional text NOT NULL,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: medico_especialidad; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medico_especialidad (
    medico_id bigint NOT NULL,
    especialidad_id bigint NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date,
    principal boolean DEFAULT false NOT NULL
);



--
-- Name: medico_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.medico ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.medico_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: muestra; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.muestra (
    id bigint NOT NULL,
    referencia_muestra text NOT NULL,
    paciente_id bigint NOT NULL,
    fecha_toma_real date NOT NULL,
    hora_toma_real time without time zone,
    hora_no_registrada boolean DEFAULT false NOT NULL,
    fecha_hora_ingreso_sistema timestamp with time zone NOT NULL,
    motivo_correccion text,
    usuario_modificacion_id bigint,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT muestra_check CHECK ((hora_no_registrada OR (hora_toma_real IS NOT NULL))),
    CONSTRAINT muestra_check1 CHECK (((NOT hora_no_registrada) OR (hora_toma_real IS NULL)))
);



--
-- Name: muestra_estudio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.muestra_estudio (
    muestra_id bigint NOT NULL,
    estudio_id bigint NOT NULL
);



--
-- Name: muestra_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.muestra ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.muestra_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: paciente; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.paciente (
    id bigint NOT NULL,
    tipo_documento text,
    numero_documento text,
    sin_documento boolean DEFAULT false NOT NULL,
    nombre_completo text NOT NULL,
    fecha_nacimiento date NOT NULL,
    sexo text NOT NULL,
    establecimiento_procedencia_id bigint,
    estado text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT paciente_check CHECK (((NOT sin_documento) OR (numero_documento IS NULL))),
    CONSTRAINT paciente_check1 CHECK (((numero_documento IS NULL) OR (tipo_documento IS NOT NULL)))
);



--
-- Name: paciente_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.paciente ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.paciente_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: parametro_plantilla; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parametro_plantilla (
    id bigint NOT NULL,
    plantilla_version_id bigint NOT NULL,
    nombre text NOT NULL,
    codigo text NOT NULL,
    tipo_entrada text NOT NULL,
    unidad text,
    rango_referencia_texto text,
    valor_minimo numeric,
    valor_maximo numeric,
    obligatorio boolean DEFAULT false NOT NULL,
    orden integer NOT NULL
);



--
-- Name: parametro_plantilla_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.parametro_plantilla ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.parametro_plantilla_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: permiso; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.permiso (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    descripcion text
);



--
-- Name: permiso_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.permiso ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.permiso_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: plantilla_examen; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plantilla_examen (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    servicio_id bigint NOT NULL,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: plantilla_examen_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.plantilla_examen ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.plantilla_examen_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: plantilla_examen_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plantilla_examen_version (
    id bigint NOT NULL,
    plantilla_examen_id bigint NOT NULL,
    numero_version integer NOT NULL,
    estado text NOT NULL,
    fecha_activacion timestamp with time zone,
    usuario_activacion_id bigint,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);



--
-- Name: plantilla_examen_version_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.plantilla_examen_version ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.plantilla_examen_version_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: politica_conservacion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.politica_conservacion (
    id bigint NOT NULL,
    modulo_documento text NOT NULL,
    plazo interval NOT NULL,
    fecha_aprobacion date NOT NULL,
    estado text NOT NULL,
    responsable text NOT NULL
);



--
-- Name: politica_conservacion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.politica_conservacion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.politica_conservacion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: respaldo_ejecucion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.respaldo_ejecucion (
    id bigint NOT NULL,
    fecha_hora_inicio timestamp with time zone NOT NULL,
    fecha_hora_finalizacion timestamp with time zone,
    estado text NOT NULL,
    fecha_cubre_hasta timestamp with time zone,
    responsable text NOT NULL,
    detalle text
);



--
-- Name: respaldo_ejecucion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.respaldo_ejecucion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.respaldo_ejecucion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: resultado_laboratorio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resultado_laboratorio (
    id bigint NOT NULL,
    estudio_id bigint NOT NULL,
    plantilla_version_id bigint NOT NULL,
    observaciones_generales text
);



--
-- Name: resultado_laboratorio_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.resultado_laboratorio ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.resultado_laboratorio_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: rol; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rol (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    descripcion text,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: rol_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.rol ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.rol_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: rol_permiso; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rol_permiso (
    rol_id bigint NOT NULL,
    permiso_id bigint NOT NULL
);



--
-- Name: rrhh_ausencia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rrhh_ausencia (
    id bigint NOT NULL,
    trabajador_id bigint NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    tipo text NOT NULL,
    motivo text,
    usuario_responsable_id bigint
);



--
-- Name: rrhh_ausencia_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.rrhh_ausencia ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.rrhh_ausencia_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: rrhh_feriado; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rrhh_feriado (
    id bigint NOT NULL,
    fecha date NOT NULL,
    descripcion text NOT NULL,
    ambito text
);



--
-- Name: rrhh_feriado_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.rrhh_feriado ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.rrhh_feriado_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: rrhh_marcacion_asistencia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rrhh_marcacion_asistencia (
    id bigint NOT NULL,
    trabajador_id bigint NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    tipo text NOT NULL,
    origen text,
    importacion_id bigint,
    referencia_origen text
);



--
-- Name: rrhh_marcacion_asistencia_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.rrhh_marcacion_asistencia ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.rrhh_marcacion_asistencia_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: servicio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.servicio (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    tipo text NOT NULL,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: servicio_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.servicio ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.servicio_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: sesion_usuario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sesion_usuario (
    id bigint NOT NULL,
    usuario_id bigint NOT NULL,
    fecha_inicio timestamp with time zone NOT NULL,
    fecha_expiracion timestamp with time zone,
    fecha_revocacion timestamp with time zone,
    estado text NOT NULL,
    ultimo_uso_at timestamp with time zone
);



--
-- Name: sesion_usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.sesion_usuario ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.sesion_usuario_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: solicitud; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solicitud (
    id bigint NOT NULL,
    referencia text NOT NULL,
    paciente_id bigint NOT NULL,
    referencia_papel_formulario text,
    fecha_solicitud timestamp with time zone NOT NULL,
    establecimiento_solicitante_id bigint,
    establecimiento_solicitante_nombre_snapshot text,
    medico_solicitante_id bigint,
    medico_solicitante_nombre_snapshot text,
    diagnostico_principal text,
    prioridad text NOT NULL,
    clave_idempotencia text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);



--
-- Name: solicitud_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.solicitud ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.solicitud_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tipo_estudio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tipo_estudio (
    id bigint NOT NULL,
    codigo text NOT NULL,
    nombre text NOT NULL,
    servicio_id bigint NOT NULL,
    requiere_muestra boolean DEFAULT false NOT NULL,
    requiere_informe boolean DEFAULT false NOT NULL,
    requiere_archivos boolean DEFAULT false NOT NULL,
    activo boolean DEFAULT true NOT NULL
);



--
-- Name: tipo_estudio_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.tipo_estudio ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tipo_estudio_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: trabajador; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.trabajador (
    id bigint NOT NULL,
    identificador text NOT NULL,
    nombre_completo text NOT NULL,
    estado text NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date
);



--
-- Name: trabajador_estado_historial; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.trabajador_estado_historial (
    id bigint NOT NULL,
    trabajador_id bigint NOT NULL,
    estado text NOT NULL,
    fecha_vigencia date NOT NULL
);



--
-- Name: trabajador_estado_historial_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.trabajador_estado_historial ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.trabajador_estado_historial_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: trabajador_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.trabajador ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.trabajador_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: transcripcion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transcripcion (
    id bigint NOT NULL,
    audio_id bigint NOT NULL,
    texto text NOT NULL,
    modelo text NOT NULL,
    version_modelo text NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    estado text NOT NULL
);



--
-- Name: transcripcion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.transcripcion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.transcripcion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: turno_atencion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.turno_atencion (
    id bigint NOT NULL,
    paciente_id bigint NOT NULL,
    especialidad_id bigint NOT NULL,
    medico_id bigint,
    fecha date NOT NULL,
    hora_programada time without time zone NOT NULL,
    numero_ficha text,
    estado text NOT NULL,
    jornada text,
    observaciones text
);



--
-- Name: turno_atencion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.turno_atencion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.turno_atencion_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuario (
    id bigint NOT NULL,
    identificador_acceso text NOT NULL,
    contrasena_hash text NOT NULL,
    rol_id bigint NOT NULL,
    trabajador_id bigint NOT NULL,
    estado text NOT NULL,
    ultimo_acceso_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);



--
-- Name: usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.usuario ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.usuario_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: version_resultado; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.version_resultado (
    id bigint NOT NULL,
    resultado_id bigint NOT NULL,
    numero_version integer NOT NULL,
    estado text NOT NULL,
    motivo_rectificacion text,
    usuario_publicacion_id bigint,
    fecha_hora_publicacion timestamp with time zone
);



--
-- Name: version_resultado_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.version_resultado ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.version_resultado_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: vista_solicitud_estado; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.vista_solicitud_estado AS
SELECT
    NULL::bigint AS solicitud_id,
    NULL::text AS referencia,
    NULL::text AS prioridad,
    NULL::text AS estado_solicitud,
    NULL::bigint[] AS estudios_pendientes;



--
-- Data for Name: embeddings; Type: TABLE DATA; Schema: meta; Owner: postgres
--



--
-- Data for Name: migrations; Type: TABLE DATA; Schema: meta; Owner: postgres
--



--
-- Data for Name: archivo_imagen; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: asignacion_horario; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: auditoria_accion; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: consulta; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: consulta_audio; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: consulta_diagnostico; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: correccion_paciente_consulta; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: correccion_paciente_estudio; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: correccion_paciente_muestra; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: correccion_paciente_receta; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: correccion_paciente_solicitud; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: detalle_valor_resultado; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: diagnostico_cie10; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: especialidad; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: establecimiento; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: estadistica_indicador; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: estadistica_regla_correspondencia; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: estadistica_reporte; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: estadistica_reporte_fuente; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: estadistica_reporte_version; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: estudio_solicitado; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: evento_atencion; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: farmacia_entrega; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: farmacia_entrega_detalle; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: farmacia_receta; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: farmacia_receta_detalle; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: farmacia_receta_version; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: horario; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: horario_jornada; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: ia_fuente; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: ia_generacion; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: importacion_archivo; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: importacion_detalle; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: informe_imagen; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: medicamento; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: medico; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: medico_especialidad; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: muestra; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: muestra_estudio; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: paciente; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: parametro_plantilla; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: permiso; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (1, 'crear', 'Crear', 'Permiso para crear registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (2, 'modificar', 'Modificar', 'Permiso para modificar registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (3, 'publicar', 'Publicar', 'Permiso para publicar registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (4, 'rectificar', 'Rectificar', 'Permiso para rectificar registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (5, 'invalidar', 'Invalidar', 'Permiso para invalidar registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (6, 'anular', 'Anular', 'Permiso para anular registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (7, 'consultar', 'Consultar', 'Permiso para consultar registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (8, 'acceder', 'Acceder', 'Permiso para acceder a registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (9, 'exportar', 'Exportar', 'Permiso para exportar registros');
INSERT INTO public.permiso OVERRIDING SYSTEM VALUE VALUES (10, 'importar', 'Importar', 'Permiso para importar registros');


--
-- Data for Name: plantilla_examen; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: plantilla_examen_version; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: politica_conservacion; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: respaldo_ejecucion; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: resultado_laboratorio; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (1, 'medico', 'Médico', 'Rol para médicos', true);
INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (2, 'laboratorio', 'Personal de Laboratorio', 'Rol para personal de laboratorio', true);
INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (3, 'imagenes', 'Personal de Imágenes', 'Rol para personal de imágenes', true);
INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (4, 'farmacia', 'Farmacia', 'Rol para personal de farmacia', true);
INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (5, 'rrhh', 'Recursos Humanos', 'Rol para personal de recursos humanos', true);
INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (6, 'estadistica', 'Estadística', 'Rol para personal de estadística', true);
INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (7, 'accesos', 'Responsable de Accesos', 'Rol para responsables de accesos', true);
INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (8, 'direccion', 'Dirección', 'Rol para directores', true);
INSERT INTO public.rol OVERRIDING SYSTEM VALUE VALUES (9, 'administracion', 'Administración', 'Rol para personal administrativo', true);


--
-- Data for Name: rol_permiso; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: rrhh_ausencia; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: rrhh_feriado; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: rrhh_marcacion_asistencia; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: servicio; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: sesion_usuario; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: solicitud; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: tipo_estudio; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: trabajador; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: trabajador_estado_historial; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: transcripcion; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: turno_atencion; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: version_resultado; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Name: archivo_imagen_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.archivo_imagen_id_seq', 1, false);


--
-- Name: asignacion_horario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.asignacion_horario_id_seq', 1, false);


--
-- Name: auditoria_accion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auditoria_accion_id_seq', 1, false);


--
-- Name: consulta_audio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.consulta_audio_id_seq', 1, false);


--
-- Name: consulta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.consulta_id_seq', 1, false);


--
-- Name: correccion_paciente_consulta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.correccion_paciente_consulta_id_seq', 1, false);


--
-- Name: correccion_paciente_estudio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.correccion_paciente_estudio_id_seq', 1, false);


--
-- Name: correccion_paciente_muestra_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.correccion_paciente_muestra_id_seq', 1, false);


--
-- Name: correccion_paciente_receta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.correccion_paciente_receta_id_seq', 1, false);


--
-- Name: correccion_paciente_solicitud_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.correccion_paciente_solicitud_id_seq', 1, false);


--
-- Name: detalle_valor_resultado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.detalle_valor_resultado_id_seq', 1, false);


--
-- Name: diagnostico_cie10_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.diagnostico_cie10_id_seq', 1, false);


--
-- Name: especialidad_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.especialidad_id_seq', 1, false);


--
-- Name: establecimiento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.establecimiento_id_seq', 1, false);


--
-- Name: estadistica_indicador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.estadistica_indicador_id_seq', 1, false);


--
-- Name: estadistica_regla_correspondencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.estadistica_regla_correspondencia_id_seq', 1, false);


--
-- Name: estadistica_reporte_fuente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.estadistica_reporte_fuente_id_seq', 1, false);


--
-- Name: estadistica_reporte_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.estadistica_reporte_id_seq', 1, false);


--
-- Name: estadistica_reporte_version_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.estadistica_reporte_version_id_seq', 1, false);


--
-- Name: estudio_solicitado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.estudio_solicitado_id_seq', 1, false);


--
-- Name: evento_atencion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.evento_atencion_id_seq', 1, false);


--
-- Name: farmacia_entrega_detalle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.farmacia_entrega_detalle_id_seq', 1, false);


--
-- Name: farmacia_entrega_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.farmacia_entrega_id_seq', 1, false);


--
-- Name: farmacia_receta_detalle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.farmacia_receta_detalle_id_seq', 1, false);


--
-- Name: farmacia_receta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.farmacia_receta_id_seq', 1, false);


--
-- Name: farmacia_receta_version_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.farmacia_receta_version_id_seq', 1, false);


--
-- Name: horario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.horario_id_seq', 1, false);


--
-- Name: horario_jornada_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.horario_jornada_id_seq', 1, false);


--
-- Name: ia_fuente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ia_fuente_id_seq', 1, false);


--
-- Name: ia_generacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ia_generacion_id_seq', 1, false);


--
-- Name: importacion_archivo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.importacion_archivo_id_seq', 1, false);


--
-- Name: importacion_detalle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.importacion_detalle_id_seq', 1, false);


--
-- Name: informe_imagen_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.informe_imagen_id_seq', 1, false);


--
-- Name: medicamento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.medicamento_id_seq', 1, false);


--
-- Name: medico_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.medico_id_seq', 1, false);


--
-- Name: muestra_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.muestra_id_seq', 1, false);


--
-- Name: paciente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.paciente_id_seq', 1, false);


--
-- Name: parametro_plantilla_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parametro_plantilla_id_seq', 1, false);


--
-- Name: permiso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.permiso_id_seq', 33, true);


--
-- Name: plantilla_examen_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.plantilla_examen_id_seq', 1, false);


--
-- Name: plantilla_examen_version_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.plantilla_examen_version_id_seq', 1, false);


--
-- Name: politica_conservacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.politica_conservacion_id_seq', 1, false);


--
-- Name: respaldo_ejecucion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.respaldo_ejecucion_id_seq', 1, false);


--
-- Name: resultado_laboratorio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.resultado_laboratorio_id_seq', 1, false);


--
-- Name: rol_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rol_id_seq', 33, true);


--
-- Name: rrhh_ausencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rrhh_ausencia_id_seq', 1, false);


--
-- Name: rrhh_feriado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rrhh_feriado_id_seq', 1, false);


--
-- Name: rrhh_marcacion_asistencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rrhh_marcacion_asistencia_id_seq', 1, false);


--
-- Name: servicio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.servicio_id_seq', 1, false);


--
-- Name: sesion_usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sesion_usuario_id_seq', 1, false);


--
-- Name: solicitud_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solicitud_id_seq', 1, false);


--
-- Name: tipo_estudio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tipo_estudio_id_seq', 1, false);


--
-- Name: trabajador_estado_historial_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.trabajador_estado_historial_id_seq', 1, false);


--
-- Name: trabajador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.trabajador_id_seq', 1, false);


--
-- Name: transcripcion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transcripcion_id_seq', 1, false);


--
-- Name: turno_atencion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.turno_atencion_id_seq', 1, false);


--
-- Name: usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuario_id_seq', 1, false);


--
-- Name: version_resultado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.version_resultado_id_seq', 1, false);


--
-- Name: archivo_imagen archivo_imagen_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archivo_imagen
    ADD CONSTRAINT archivo_imagen_pkey PRIMARY KEY (id);


--
-- Name: asignacion_horario asignacion_horario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asignacion_horario
    ADD CONSTRAINT asignacion_horario_pkey PRIMARY KEY (id);


--
-- Name: auditoria_accion auditoria_accion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditoria_accion
    ADD CONSTRAINT auditoria_accion_pkey PRIMARY KEY (id);


--
-- Name: consulta_audio consulta_audio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_audio
    ADD CONSTRAINT consulta_audio_pkey PRIMARY KEY (id);


--
-- Name: consulta_diagnostico consulta_diagnostico_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_diagnostico
    ADD CONSTRAINT consulta_diagnostico_pkey PRIMARY KEY (consulta_id, diagnostico_id);


--
-- Name: consulta consulta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta
    ADD CONSTRAINT consulta_pkey PRIMARY KEY (id);


--
-- Name: correccion_paciente_consulta correccion_paciente_consulta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_consulta
    ADD CONSTRAINT correccion_paciente_consulta_pkey PRIMARY KEY (id);


--
-- Name: correccion_paciente_estudio correccion_paciente_estudio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_estudio
    ADD CONSTRAINT correccion_paciente_estudio_pkey PRIMARY KEY (id);


--
-- Name: correccion_paciente_muestra correccion_paciente_muestra_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_muestra
    ADD CONSTRAINT correccion_paciente_muestra_pkey PRIMARY KEY (id);


--
-- Name: correccion_paciente_receta correccion_paciente_receta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_receta
    ADD CONSTRAINT correccion_paciente_receta_pkey PRIMARY KEY (id);


--
-- Name: correccion_paciente_solicitud correccion_paciente_solicitud_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_solicitud
    ADD CONSTRAINT correccion_paciente_solicitud_pkey PRIMARY KEY (id);


--
-- Name: detalle_valor_resultado detalle_valor_resultado_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_valor_resultado
    ADD CONSTRAINT detalle_valor_resultado_pkey PRIMARY KEY (id);


--
-- Name: diagnostico_cie10 diagnostico_cie10_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnostico_cie10
    ADD CONSTRAINT diagnostico_cie10_codigo_key UNIQUE (codigo);


--
-- Name: diagnostico_cie10 diagnostico_cie10_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnostico_cie10
    ADD CONSTRAINT diagnostico_cie10_pkey PRIMARY KEY (id);


--
-- Name: especialidad especialidad_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.especialidad
    ADD CONSTRAINT especialidad_codigo_key UNIQUE (codigo);


--
-- Name: especialidad especialidad_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.especialidad
    ADD CONSTRAINT especialidad_pkey PRIMARY KEY (id);


--
-- Name: establecimiento establecimiento_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.establecimiento
    ADD CONSTRAINT establecimiento_codigo_key UNIQUE (codigo);


--
-- Name: establecimiento establecimiento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.establecimiento
    ADD CONSTRAINT establecimiento_pkey PRIMARY KEY (id);


--
-- Name: estadistica_indicador estadistica_indicador_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_indicador
    ADD CONSTRAINT estadistica_indicador_codigo_key UNIQUE (codigo);


--
-- Name: estadistica_indicador estadistica_indicador_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_indicador
    ADD CONSTRAINT estadistica_indicador_pkey PRIMARY KEY (id);


--
-- Name: estadistica_regla_correspondencia estadistica_regla_correspondencia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_regla_correspondencia
    ADD CONSTRAINT estadistica_regla_correspondencia_pkey PRIMARY KEY (id);


--
-- Name: estadistica_reporte_fuente estadistica_reporte_fuente_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_reporte_fuente
    ADD CONSTRAINT estadistica_reporte_fuente_pkey PRIMARY KEY (id);


--
-- Name: estadistica_reporte estadistica_reporte_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_reporte
    ADD CONSTRAINT estadistica_reporte_pkey PRIMARY KEY (id);


--
-- Name: estadistica_reporte_version estadistica_reporte_version_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_reporte_version
    ADD CONSTRAINT estadistica_reporte_version_pkey PRIMARY KEY (id);


--
-- Name: estadistica_reporte_version estadistica_reporte_version_reporte_id_numero_version_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_reporte_version
    ADD CONSTRAINT estadistica_reporte_version_reporte_id_numero_version_key UNIQUE (reporte_id, numero_version);


--
-- Name: estudio_solicitado estudio_solicitado_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudio_solicitado
    ADD CONSTRAINT estudio_solicitado_pkey PRIMARY KEY (id);


--
-- Name: estudio_solicitado estudio_solicitado_referencia_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudio_solicitado
    ADD CONSTRAINT estudio_solicitado_referencia_key UNIQUE (referencia);


--
-- Name: evento_atencion evento_atencion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evento_atencion
    ADD CONSTRAINT evento_atencion_pkey PRIMARY KEY (id);


--
-- Name: farmacia_entrega farmacia_entrega_clave_idempotencia_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_entrega
    ADD CONSTRAINT farmacia_entrega_clave_idempotencia_key UNIQUE (clave_idempotencia);


--
-- Name: farmacia_entrega_detalle farmacia_entrega_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_entrega_detalle
    ADD CONSTRAINT farmacia_entrega_detalle_pkey PRIMARY KEY (id);


--
-- Name: farmacia_entrega farmacia_entrega_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_entrega
    ADD CONSTRAINT farmacia_entrega_pkey PRIMARY KEY (id);


--
-- Name: farmacia_receta_detalle farmacia_receta_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta_detalle
    ADD CONSTRAINT farmacia_receta_detalle_pkey PRIMARY KEY (id);


--
-- Name: farmacia_receta farmacia_receta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta
    ADD CONSTRAINT farmacia_receta_pkey PRIMARY KEY (id);


--
-- Name: farmacia_receta_version farmacia_receta_version_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta_version
    ADD CONSTRAINT farmacia_receta_version_pkey PRIMARY KEY (id);


--
-- Name: farmacia_receta_version farmacia_receta_version_receta_id_numero_version_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta_version
    ADD CONSTRAINT farmacia_receta_version_receta_id_numero_version_key UNIQUE (receta_id, numero_version);


--
-- Name: horario_jornada horario_jornada_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.horario_jornada
    ADD CONSTRAINT horario_jornada_pkey PRIMARY KEY (id);


--
-- Name: horario horario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.horario
    ADD CONSTRAINT horario_pkey PRIMARY KEY (id);


--
-- Name: ia_fuente ia_fuente_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ia_fuente
    ADD CONSTRAINT ia_fuente_pkey PRIMARY KEY (id);


--
-- Name: ia_generacion ia_generacion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ia_generacion
    ADD CONSTRAINT ia_generacion_pkey PRIMARY KEY (id);


--
-- Name: importacion_archivo importacion_archivo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.importacion_archivo
    ADD CONSTRAINT importacion_archivo_pkey PRIMARY KEY (id);


--
-- Name: importacion_detalle importacion_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.importacion_detalle
    ADD CONSTRAINT importacion_detalle_pkey PRIMARY KEY (id);


--
-- Name: informe_imagen informe_imagen_estudio_id_numero_version_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.informe_imagen
    ADD CONSTRAINT informe_imagen_estudio_id_numero_version_key UNIQUE (estudio_id, numero_version);


--
-- Name: informe_imagen informe_imagen_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.informe_imagen
    ADD CONSTRAINT informe_imagen_pkey PRIMARY KEY (id);


--
-- Name: medicamento medicamento_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medicamento
    ADD CONSTRAINT medicamento_codigo_key UNIQUE (codigo);


--
-- Name: medicamento medicamento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medicamento
    ADD CONSTRAINT medicamento_pkey PRIMARY KEY (id);


--
-- Name: medico_especialidad medico_especialidad_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medico_especialidad
    ADD CONSTRAINT medico_especialidad_pkey PRIMARY KEY (medico_id, especialidad_id);


--
-- Name: medico medico_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medico
    ADD CONSTRAINT medico_pkey PRIMARY KEY (id);


--
-- Name: medico medico_trabajador_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medico
    ADD CONSTRAINT medico_trabajador_id_key UNIQUE (trabajador_id);


--
-- Name: muestra_estudio muestra_estudio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.muestra_estudio
    ADD CONSTRAINT muestra_estudio_pkey PRIMARY KEY (muestra_id, estudio_id);


--
-- Name: muestra muestra_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.muestra
    ADD CONSTRAINT muestra_pkey PRIMARY KEY (id);


--
-- Name: muestra muestra_referencia_muestra_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.muestra
    ADD CONSTRAINT muestra_referencia_muestra_key UNIQUE (referencia_muestra);


--
-- Name: paciente paciente_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paciente
    ADD CONSTRAINT paciente_pkey PRIMARY KEY (id);


--
-- Name: parametro_plantilla parametro_plantilla_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parametro_plantilla
    ADD CONSTRAINT parametro_plantilla_pkey PRIMARY KEY (id);


--
-- Name: permiso permiso_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_codigo_key UNIQUE (codigo);


--
-- Name: permiso permiso_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_pkey PRIMARY KEY (id);


--
-- Name: plantilla_examen plantilla_examen_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantilla_examen
    ADD CONSTRAINT plantilla_examen_codigo_key UNIQUE (codigo);


--
-- Name: plantilla_examen plantilla_examen_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantilla_examen
    ADD CONSTRAINT plantilla_examen_pkey PRIMARY KEY (id);


--
-- Name: plantilla_examen_version plantilla_examen_version_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantilla_examen_version
    ADD CONSTRAINT plantilla_examen_version_pkey PRIMARY KEY (id);


--
-- Name: plantilla_examen_version plantilla_examen_version_plantilla_examen_id_numero_version_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantilla_examen_version
    ADD CONSTRAINT plantilla_examen_version_plantilla_examen_id_numero_version_key UNIQUE (plantilla_examen_id, numero_version);


--
-- Name: politica_conservacion politica_conservacion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.politica_conservacion
    ADD CONSTRAINT politica_conservacion_pkey PRIMARY KEY (id);


--
-- Name: respaldo_ejecucion respaldo_ejecucion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.respaldo_ejecucion
    ADD CONSTRAINT respaldo_ejecucion_pkey PRIMARY KEY (id);


--
-- Name: resultado_laboratorio resultado_laboratorio_estudio_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resultado_laboratorio
    ADD CONSTRAINT resultado_laboratorio_estudio_id_key UNIQUE (estudio_id);


--
-- Name: resultado_laboratorio resultado_laboratorio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resultado_laboratorio
    ADD CONSTRAINT resultado_laboratorio_pkey PRIMARY KEY (id);


--
-- Name: rol rol_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_codigo_key UNIQUE (codigo);


--
-- Name: rol_permiso rol_permiso_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (rol_id, permiso_id);


--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id);


--
-- Name: rrhh_ausencia rrhh_ausencia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rrhh_ausencia
    ADD CONSTRAINT rrhh_ausencia_pkey PRIMARY KEY (id);


--
-- Name: rrhh_feriado rrhh_feriado_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rrhh_feriado
    ADD CONSTRAINT rrhh_feriado_pkey PRIMARY KEY (id);


--
-- Name: rrhh_marcacion_asistencia rrhh_marcacion_asistencia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rrhh_marcacion_asistencia
    ADD CONSTRAINT rrhh_marcacion_asistencia_pkey PRIMARY KEY (id);


--
-- Name: servicio servicio_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicio
    ADD CONSTRAINT servicio_codigo_key UNIQUE (codigo);


--
-- Name: servicio servicio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicio
    ADD CONSTRAINT servicio_pkey PRIMARY KEY (id);


--
-- Name: sesion_usuario sesion_usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sesion_usuario
    ADD CONSTRAINT sesion_usuario_pkey PRIMARY KEY (id);


--
-- Name: solicitud solicitud_clave_idempotencia_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitud
    ADD CONSTRAINT solicitud_clave_idempotencia_key UNIQUE (clave_idempotencia);


--
-- Name: solicitud solicitud_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitud
    ADD CONSTRAINT solicitud_pkey PRIMARY KEY (id);


--
-- Name: solicitud solicitud_referencia_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitud
    ADD CONSTRAINT solicitud_referencia_key UNIQUE (referencia);


--
-- Name: tipo_estudio tipo_estudio_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipo_estudio
    ADD CONSTRAINT tipo_estudio_codigo_key UNIQUE (codigo);


--
-- Name: tipo_estudio tipo_estudio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipo_estudio
    ADD CONSTRAINT tipo_estudio_pkey PRIMARY KEY (id);


--
-- Name: trabajador_estado_historial trabajador_estado_historial_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajador_estado_historial
    ADD CONSTRAINT trabajador_estado_historial_pkey PRIMARY KEY (id);


--
-- Name: trabajador trabajador_identificador_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajador
    ADD CONSTRAINT trabajador_identificador_key UNIQUE (identificador);


--
-- Name: trabajador trabajador_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajador
    ADD CONSTRAINT trabajador_pkey PRIMARY KEY (id);


--
-- Name: transcripcion transcripcion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transcripcion
    ADD CONSTRAINT transcripcion_pkey PRIMARY KEY (id);


--
-- Name: turno_atencion turno_atencion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turno_atencion
    ADD CONSTRAINT turno_atencion_pkey PRIMARY KEY (id);


--
-- Name: usuario usuario_identificador_acceso_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_identificador_acceso_key UNIQUE (identificador_acceso);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);


--
-- Name: version_resultado version_resultado_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.version_resultado
    ADD CONSTRAINT version_resultado_pkey PRIMARY KEY (id);


--
-- Name: version_resultado version_resultado_resultado_id_numero_version_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.version_resultado
    ADD CONSTRAINT version_resultado_resultado_id_numero_version_key UNIQUE (resultado_id, numero_version);


--
-- Name: uq_paciente_documento; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_paciente_documento ON public.paciente USING btree (tipo_documento, numero_documento) WHERE (numero_documento IS NOT NULL);


--
-- Name: vista_solicitud_estado _RETURN; Type: RULE; Schema: public; Owner: postgres
--

CREATE OR REPLACE VIEW public.vista_solicitud_estado AS
 SELECT s.id AS solicitud_id,
    s.referencia,
    s.prioridad,
        CASE
            WHEN (count(e.id) FILTER (WHERE (e.estado = 'publicado'::text)) = count(e.id)) THEN 'completa'::text
            ELSE 'parcial'::text
        END AS estado_solicitud,
    array_agg(e.id) FILTER (WHERE (e.estado <> 'publicado'::text)) AS estudios_pendientes
   FROM (public.solicitud s
     LEFT JOIN public.estudio_solicitado e ON ((s.id = e.solicitud_id)))
  GROUP BY s.id;


--
-- Name: consulta actualizar_consulta_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER actualizar_consulta_updated_at BEFORE UPDATE ON public.consulta FOR EACH ROW EXECUTE FUNCTION public.actualizar_updated_at();


--
-- Name: paciente actualizar_paciente_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER actualizar_paciente_updated_at BEFORE UPDATE ON public.paciente FOR EACH ROW EXECUTE FUNCTION public.actualizar_updated_at();


--
-- Name: usuario actualizar_usuario_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER actualizar_usuario_updated_at BEFORE UPDATE ON public.usuario FOR EACH ROW EXECUTE FUNCTION public.actualizar_updated_at();


--
-- Name: archivo_imagen archivo_imagen_archivo_reemplazado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archivo_imagen
    ADD CONSTRAINT archivo_imagen_archivo_reemplazado_id_fkey FOREIGN KEY (archivo_reemplazado_id) REFERENCES public.archivo_imagen(id);


--
-- Name: archivo_imagen archivo_imagen_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archivo_imagen
    ADD CONSTRAINT archivo_imagen_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: archivo_imagen archivo_imagen_informe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archivo_imagen
    ADD CONSTRAINT archivo_imagen_informe_id_fkey FOREIGN KEY (informe_id) REFERENCES public.informe_imagen(id);


--
-- Name: asignacion_horario asignacion_horario_horario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asignacion_horario
    ADD CONSTRAINT asignacion_horario_horario_id_fkey FOREIGN KEY (horario_id) REFERENCES public.horario(id);


--
-- Name: asignacion_horario asignacion_horario_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asignacion_horario
    ADD CONSTRAINT asignacion_horario_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id);


--
-- Name: auditoria_accion auditoria_accion_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditoria_accion
    ADD CONSTRAINT auditoria_accion_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: consulta_audio consulta_audio_consulta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_audio
    ADD CONSTRAINT consulta_audio_consulta_id_fkey FOREIGN KEY (consulta_id) REFERENCES public.consulta(id);


--
-- Name: consulta_audio consulta_audio_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_audio
    ADD CONSTRAINT consulta_audio_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: consulta_diagnostico consulta_diagnostico_consulta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_diagnostico
    ADD CONSTRAINT consulta_diagnostico_consulta_id_fkey FOREIGN KEY (consulta_id) REFERENCES public.consulta(id);


--
-- Name: consulta_diagnostico consulta_diagnostico_diagnostico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta_diagnostico
    ADD CONSTRAINT consulta_diagnostico_diagnostico_id_fkey FOREIGN KEY (diagnostico_id) REFERENCES public.diagnostico_cie10(id);


--
-- Name: consulta consulta_especialidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta
    ADD CONSTRAINT consulta_especialidad_id_fkey FOREIGN KEY (especialidad_id) REFERENCES public.especialidad(id);


--
-- Name: consulta consulta_medico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta
    ADD CONSTRAINT consulta_medico_id_fkey FOREIGN KEY (medico_id) REFERENCES public.medico(id);


--
-- Name: consulta consulta_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta
    ADD CONSTRAINT consulta_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.paciente(id);


--
-- Name: consulta consulta_turno_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consulta
    ADD CONSTRAINT consulta_turno_id_fkey FOREIGN KEY (turno_id) REFERENCES public.turno_atencion(id);


--
-- Name: correccion_paciente_consulta correccion_paciente_consulta_consulta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_consulta
    ADD CONSTRAINT correccion_paciente_consulta_consulta_id_fkey FOREIGN KEY (consulta_id) REFERENCES public.consulta(id);


--
-- Name: correccion_paciente_consulta correccion_paciente_consulta_paciente_anterior_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_consulta
    ADD CONSTRAINT correccion_paciente_consulta_paciente_anterior_id_fkey FOREIGN KEY (paciente_anterior_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_consulta correccion_paciente_consulta_paciente_nuevo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_consulta
    ADD CONSTRAINT correccion_paciente_consulta_paciente_nuevo_id_fkey FOREIGN KEY (paciente_nuevo_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_consulta correccion_paciente_consulta_usuario_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_consulta
    ADD CONSTRAINT correccion_paciente_consulta_usuario_responsable_id_fkey FOREIGN KEY (usuario_responsable_id) REFERENCES public.usuario(id);


--
-- Name: correccion_paciente_estudio correccion_paciente_estudio_estudio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_estudio
    ADD CONSTRAINT correccion_paciente_estudio_estudio_id_fkey FOREIGN KEY (estudio_id) REFERENCES public.estudio_solicitado(id);


--
-- Name: correccion_paciente_estudio correccion_paciente_estudio_paciente_anterior_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_estudio
    ADD CONSTRAINT correccion_paciente_estudio_paciente_anterior_id_fkey FOREIGN KEY (paciente_anterior_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_estudio correccion_paciente_estudio_paciente_nuevo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_estudio
    ADD CONSTRAINT correccion_paciente_estudio_paciente_nuevo_id_fkey FOREIGN KEY (paciente_nuevo_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_estudio correccion_paciente_estudio_usuario_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_estudio
    ADD CONSTRAINT correccion_paciente_estudio_usuario_responsable_id_fkey FOREIGN KEY (usuario_responsable_id) REFERENCES public.usuario(id);


--
-- Name: correccion_paciente_muestra correccion_paciente_muestra_muestra_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_muestra
    ADD CONSTRAINT correccion_paciente_muestra_muestra_id_fkey FOREIGN KEY (muestra_id) REFERENCES public.muestra(id);


--
-- Name: correccion_paciente_muestra correccion_paciente_muestra_paciente_anterior_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_muestra
    ADD CONSTRAINT correccion_paciente_muestra_paciente_anterior_id_fkey FOREIGN KEY (paciente_anterior_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_muestra correccion_paciente_muestra_paciente_nuevo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_muestra
    ADD CONSTRAINT correccion_paciente_muestra_paciente_nuevo_id_fkey FOREIGN KEY (paciente_nuevo_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_muestra correccion_paciente_muestra_usuario_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_muestra
    ADD CONSTRAINT correccion_paciente_muestra_usuario_responsable_id_fkey FOREIGN KEY (usuario_responsable_id) REFERENCES public.usuario(id);


--
-- Name: correccion_paciente_receta correccion_paciente_receta_paciente_anterior_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_receta
    ADD CONSTRAINT correccion_paciente_receta_paciente_anterior_id_fkey FOREIGN KEY (paciente_anterior_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_receta correccion_paciente_receta_paciente_nuevo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_receta
    ADD CONSTRAINT correccion_paciente_receta_paciente_nuevo_id_fkey FOREIGN KEY (paciente_nuevo_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_receta correccion_paciente_receta_receta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_receta
    ADD CONSTRAINT correccion_paciente_receta_receta_id_fkey FOREIGN KEY (receta_id) REFERENCES public.farmacia_receta(id);


--
-- Name: correccion_paciente_receta correccion_paciente_receta_usuario_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_receta
    ADD CONSTRAINT correccion_paciente_receta_usuario_responsable_id_fkey FOREIGN KEY (usuario_responsable_id) REFERENCES public.usuario(id);


--
-- Name: correccion_paciente_solicitud correccion_paciente_solicitud_paciente_anterior_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_solicitud
    ADD CONSTRAINT correccion_paciente_solicitud_paciente_anterior_id_fkey FOREIGN KEY (paciente_anterior_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_solicitud correccion_paciente_solicitud_paciente_nuevo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_solicitud
    ADD CONSTRAINT correccion_paciente_solicitud_paciente_nuevo_id_fkey FOREIGN KEY (paciente_nuevo_id) REFERENCES public.paciente(id);


--
-- Name: correccion_paciente_solicitud correccion_paciente_solicitud_solicitud_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_solicitud
    ADD CONSTRAINT correccion_paciente_solicitud_solicitud_id_fkey FOREIGN KEY (solicitud_id) REFERENCES public.solicitud(id);


--
-- Name: correccion_paciente_solicitud correccion_paciente_solicitud_usuario_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correccion_paciente_solicitud
    ADD CONSTRAINT correccion_paciente_solicitud_usuario_responsable_id_fkey FOREIGN KEY (usuario_responsable_id) REFERENCES public.usuario(id);


--
-- Name: detalle_valor_resultado detalle_valor_resultado_parametro_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_valor_resultado
    ADD CONSTRAINT detalle_valor_resultado_parametro_id_fkey FOREIGN KEY (parametro_id) REFERENCES public.parametro_plantilla(id);


--
-- Name: detalle_valor_resultado detalle_valor_resultado_version_resultado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_valor_resultado
    ADD CONSTRAINT detalle_valor_resultado_version_resultado_id_fkey FOREIGN KEY (version_resultado_id) REFERENCES public.version_resultado(id);


--
-- Name: estadistica_regla_correspondencia estadistica_regla_correspondencia_indicador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_regla_correspondencia
    ADD CONSTRAINT estadistica_regla_correspondencia_indicador_id_fkey FOREIGN KEY (indicador_id) REFERENCES public.estadistica_indicador(id);


--
-- Name: estadistica_reporte_fuente estadistica_reporte_fuente_reporte_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_reporte_fuente
    ADD CONSTRAINT estadistica_reporte_fuente_reporte_version_id_fkey FOREIGN KEY (reporte_version_id) REFERENCES public.estadistica_reporte_version(id);


--
-- Name: estadistica_reporte_version estadistica_reporte_version_reporte_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_reporte_version
    ADD CONSTRAINT estadistica_reporte_version_reporte_id_fkey FOREIGN KEY (reporte_id) REFERENCES public.estadistica_reporte(id);


--
-- Name: estadistica_reporte_version estadistica_reporte_version_usuario_confirmacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estadistica_reporte_version
    ADD CONSTRAINT estadistica_reporte_version_usuario_confirmacion_id_fkey FOREIGN KEY (usuario_confirmacion_id) REFERENCES public.usuario(id);


--
-- Name: estudio_solicitado estudio_solicitado_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudio_solicitado
    ADD CONSTRAINT estudio_solicitado_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.paciente(id);


--
-- Name: estudio_solicitado estudio_solicitado_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudio_solicitado
    ADD CONSTRAINT estudio_solicitado_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicio(id);


--
-- Name: estudio_solicitado estudio_solicitado_solicitud_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudio_solicitado
    ADD CONSTRAINT estudio_solicitado_solicitud_id_fkey FOREIGN KEY (solicitud_id) REFERENCES public.solicitud(id);


--
-- Name: estudio_solicitado estudio_solicitado_tipo_estudio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estudio_solicitado
    ADD CONSTRAINT estudio_solicitado_tipo_estudio_id_fkey FOREIGN KEY (tipo_estudio_id) REFERENCES public.tipo_estudio(id);


--
-- Name: evento_atencion evento_atencion_consulta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evento_atencion
    ADD CONSTRAINT evento_atencion_consulta_id_fkey FOREIGN KEY (consulta_id) REFERENCES public.consulta(id);


--
-- Name: evento_atencion evento_atencion_turno_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evento_atencion
    ADD CONSTRAINT evento_atencion_turno_id_fkey FOREIGN KEY (turno_id) REFERENCES public.turno_atencion(id);


--
-- Name: evento_atencion evento_atencion_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evento_atencion
    ADD CONSTRAINT evento_atencion_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: farmacia_entrega_detalle farmacia_entrega_detalle_entrega_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_entrega_detalle
    ADD CONSTRAINT farmacia_entrega_detalle_entrega_id_fkey FOREIGN KEY (entrega_id) REFERENCES public.farmacia_entrega(id);


--
-- Name: farmacia_entrega_detalle farmacia_entrega_detalle_receta_detalle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_entrega_detalle
    ADD CONSTRAINT farmacia_entrega_detalle_receta_detalle_id_fkey FOREIGN KEY (receta_detalle_id) REFERENCES public.farmacia_receta_detalle(id);


--
-- Name: farmacia_entrega farmacia_entrega_entregado_por_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_entrega
    ADD CONSTRAINT farmacia_entrega_entregado_por_usuario_id_fkey FOREIGN KEY (entregado_por_usuario_id) REFERENCES public.usuario(id);


--
-- Name: farmacia_entrega farmacia_entrega_receta_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_entrega
    ADD CONSTRAINT farmacia_entrega_receta_version_id_fkey FOREIGN KEY (receta_version_id) REFERENCES public.farmacia_receta_version(id);


--
-- Name: farmacia_receta_detalle farmacia_receta_detalle_medicamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta_detalle
    ADD CONSTRAINT farmacia_receta_detalle_medicamento_id_fkey FOREIGN KEY (medicamento_id) REFERENCES public.medicamento(id);


--
-- Name: farmacia_receta_detalle farmacia_receta_detalle_receta_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta_detalle
    ADD CONSTRAINT farmacia_receta_detalle_receta_version_id_fkey FOREIGN KEY (receta_version_id) REFERENCES public.farmacia_receta_version(id);


--
-- Name: farmacia_receta farmacia_receta_establecimiento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta
    ADD CONSTRAINT farmacia_receta_establecimiento_id_fkey FOREIGN KEY (establecimiento_id) REFERENCES public.establecimiento(id);


--
-- Name: farmacia_receta farmacia_receta_medico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta
    ADD CONSTRAINT farmacia_receta_medico_id_fkey FOREIGN KEY (medico_id) REFERENCES public.medico(id);


--
-- Name: farmacia_receta farmacia_receta_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta
    ADD CONSTRAINT farmacia_receta_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.paciente(id);


--
-- Name: farmacia_receta_version farmacia_receta_version_receta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta_version
    ADD CONSTRAINT farmacia_receta_version_receta_id_fkey FOREIGN KEY (receta_id) REFERENCES public.farmacia_receta(id);


--
-- Name: farmacia_receta_version farmacia_receta_version_usuario_emision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.farmacia_receta_version
    ADD CONSTRAINT farmacia_receta_version_usuario_emision_id_fkey FOREIGN KEY (usuario_emision_id) REFERENCES public.usuario(id);


--
-- Name: horario_jornada horario_jornada_horario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.horario_jornada
    ADD CONSTRAINT horario_jornada_horario_id_fkey FOREIGN KEY (horario_id) REFERENCES public.horario(id);


--
-- Name: ia_fuente ia_fuente_generacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ia_fuente
    ADD CONSTRAINT ia_fuente_generacion_id_fkey FOREIGN KEY (generacion_id) REFERENCES public.ia_generacion(id);


--
-- Name: ia_generacion ia_generacion_consulta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ia_generacion
    ADD CONSTRAINT ia_generacion_consulta_id_fkey FOREIGN KEY (consulta_id) REFERENCES public.consulta(id);


--
-- Name: ia_generacion ia_generacion_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ia_generacion
    ADD CONSTRAINT ia_generacion_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.paciente(id);


--
-- Name: ia_generacion ia_generacion_usuario_revisor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ia_generacion
    ADD CONSTRAINT ia_generacion_usuario_revisor_id_fkey FOREIGN KEY (usuario_revisor_id) REFERENCES public.usuario(id);


--
-- Name: importacion_archivo importacion_archivo_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.importacion_archivo
    ADD CONSTRAINT importacion_archivo_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: importacion_detalle importacion_detalle_importacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.importacion_detalle
    ADD CONSTRAINT importacion_detalle_importacion_id_fkey FOREIGN KEY (importacion_id) REFERENCES public.importacion_archivo(id);


--
-- Name: informe_imagen informe_imagen_estudio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.informe_imagen
    ADD CONSTRAINT informe_imagen_estudio_id_fkey FOREIGN KEY (estudio_id) REFERENCES public.estudio_solicitado(id);


--
-- Name: informe_imagen informe_imagen_usuario_publicacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.informe_imagen
    ADD CONSTRAINT informe_imagen_usuario_publicacion_id_fkey FOREIGN KEY (usuario_publicacion_id) REFERENCES public.usuario(id);


--
-- Name: medico_especialidad medico_especialidad_especialidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medico_especialidad
    ADD CONSTRAINT medico_especialidad_especialidad_id_fkey FOREIGN KEY (especialidad_id) REFERENCES public.especialidad(id);


--
-- Name: medico_especialidad medico_especialidad_medico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medico_especialidad
    ADD CONSTRAINT medico_especialidad_medico_id_fkey FOREIGN KEY (medico_id) REFERENCES public.medico(id);


--
-- Name: medico medico_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medico
    ADD CONSTRAINT medico_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id);


--
-- Name: muestra_estudio muestra_estudio_estudio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.muestra_estudio
    ADD CONSTRAINT muestra_estudio_estudio_id_fkey FOREIGN KEY (estudio_id) REFERENCES public.estudio_solicitado(id);


--
-- Name: muestra_estudio muestra_estudio_muestra_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.muestra_estudio
    ADD CONSTRAINT muestra_estudio_muestra_id_fkey FOREIGN KEY (muestra_id) REFERENCES public.muestra(id);


--
-- Name: muestra muestra_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.muestra
    ADD CONSTRAINT muestra_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.paciente(id);


--
-- Name: muestra muestra_usuario_modificacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.muestra
    ADD CONSTRAINT muestra_usuario_modificacion_id_fkey FOREIGN KEY (usuario_modificacion_id) REFERENCES public.usuario(id);


--
-- Name: paciente paciente_establecimiento_procedencia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paciente
    ADD CONSTRAINT paciente_establecimiento_procedencia_id_fkey FOREIGN KEY (establecimiento_procedencia_id) REFERENCES public.establecimiento(id);


--
-- Name: parametro_plantilla parametro_plantilla_plantilla_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parametro_plantilla
    ADD CONSTRAINT parametro_plantilla_plantilla_version_id_fkey FOREIGN KEY (plantilla_version_id) REFERENCES public.plantilla_examen_version(id);


--
-- Name: plantilla_examen plantilla_examen_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantilla_examen
    ADD CONSTRAINT plantilla_examen_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicio(id);


--
-- Name: plantilla_examen_version plantilla_examen_version_plantilla_examen_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantilla_examen_version
    ADD CONSTRAINT plantilla_examen_version_plantilla_examen_id_fkey FOREIGN KEY (plantilla_examen_id) REFERENCES public.plantilla_examen(id);


--
-- Name: plantilla_examen_version plantilla_examen_version_usuario_activacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantilla_examen_version
    ADD CONSTRAINT plantilla_examen_version_usuario_activacion_id_fkey FOREIGN KEY (usuario_activacion_id) REFERENCES public.usuario(id);


--
-- Name: resultado_laboratorio resultado_laboratorio_estudio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resultado_laboratorio
    ADD CONSTRAINT resultado_laboratorio_estudio_id_fkey FOREIGN KEY (estudio_id) REFERENCES public.estudio_solicitado(id);


--
-- Name: resultado_laboratorio resultado_laboratorio_plantilla_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resultado_laboratorio
    ADD CONSTRAINT resultado_laboratorio_plantilla_version_id_fkey FOREIGN KEY (plantilla_version_id) REFERENCES public.plantilla_examen_version(id);


--
-- Name: rol_permiso rol_permiso_permiso_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_permiso_id_fkey FOREIGN KEY (permiso_id) REFERENCES public.permiso(id);


--
-- Name: rol_permiso rol_permiso_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.rol(id);


--
-- Name: rrhh_ausencia rrhh_ausencia_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rrhh_ausencia
    ADD CONSTRAINT rrhh_ausencia_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id);


--
-- Name: rrhh_ausencia rrhh_ausencia_usuario_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rrhh_ausencia
    ADD CONSTRAINT rrhh_ausencia_usuario_responsable_id_fkey FOREIGN KEY (usuario_responsable_id) REFERENCES public.usuario(id);


--
-- Name: rrhh_marcacion_asistencia rrhh_marcacion_asistencia_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rrhh_marcacion_asistencia
    ADD CONSTRAINT rrhh_marcacion_asistencia_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id);


--
-- Name: sesion_usuario sesion_usuario_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sesion_usuario
    ADD CONSTRAINT sesion_usuario_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: solicitud solicitud_establecimiento_solicitante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitud
    ADD CONSTRAINT solicitud_establecimiento_solicitante_id_fkey FOREIGN KEY (establecimiento_solicitante_id) REFERENCES public.establecimiento(id);


--
-- Name: solicitud solicitud_medico_solicitante_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitud
    ADD CONSTRAINT solicitud_medico_solicitante_id_fkey FOREIGN KEY (medico_solicitante_id) REFERENCES public.medico(id);


--
-- Name: solicitud solicitud_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitud
    ADD CONSTRAINT solicitud_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.paciente(id);


--
-- Name: tipo_estudio tipo_estudio_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipo_estudio
    ADD CONSTRAINT tipo_estudio_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicio(id);


--
-- Name: trabajador_estado_historial trabajador_estado_historial_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajador_estado_historial
    ADD CONSTRAINT trabajador_estado_historial_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id);


--
-- Name: transcripcion transcripcion_audio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transcripcion
    ADD CONSTRAINT transcripcion_audio_id_fkey FOREIGN KEY (audio_id) REFERENCES public.consulta_audio(id);


--
-- Name: turno_atencion turno_atencion_especialidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turno_atencion
    ADD CONSTRAINT turno_atencion_especialidad_id_fkey FOREIGN KEY (especialidad_id) REFERENCES public.especialidad(id);


--
-- Name: turno_atencion turno_atencion_medico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turno_atencion
    ADD CONSTRAINT turno_atencion_medico_id_fkey FOREIGN KEY (medico_id) REFERENCES public.medico(id);


--
-- Name: turno_atencion turno_atencion_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turno_atencion
    ADD CONSTRAINT turno_atencion_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.paciente(id);


--
-- Name: usuario usuario_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.rol(id);


--
-- Name: usuario usuario_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id);


--
-- Name: version_resultado version_resultado_resultado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.version_resultado
    ADD CONSTRAINT version_resultado_resultado_id_fkey FOREIGN KEY (resultado_id) REFERENCES public.resultado_laboratorio(id);


--
-- Name: version_resultado version_resultado_usuario_publicacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.version_resultado
    ADD CONSTRAINT version_resultado_usuario_publicacion_id_fkey FOREIGN KEY (usuario_publicacion_id) REFERENCES public.usuario(id);


--
-- PostgreSQL database dump complete
--



-- =====================================================================
-- A PARTIR DE AQUI: COMPLEMENTO Y CORRECCIONES
-- =====================================================================

-- =====================================================================
-- HOSPITAL SARCOBAMBA - PARTE 5: COMPLEMENTO Y CORRECCIONES
-- Se ejecuta DESPUES del script generado por database.build.
-- Compatible con PGlite / database.build:
--   sin extensiones, sin EXCLUDE, sin ENUM, sin ON DELETE CASCADE.
-- =====================================================================


-- =====================================================================
-- 1. COLUMNAS FALTANTES
-- =====================================================================

-- 1.1 Identificador interno publico del paciente (RF: identificador unico interno)
ALTER TABLE public.paciente
    ADD COLUMN IF NOT EXISTS codigo_paciente text;

UPDATE public.paciente
   SET codigo_paciente = 'PAC-' || lpad(id::text, 8, '0')
 WHERE codigo_paciente IS NULL;

ALTER TABLE public.paciente
    ALTER COLUMN codigo_paciente SET NOT NULL;

ALTER TABLE public.paciente
    ADD CONSTRAINT uq_paciente_codigo UNIQUE (codigo_paciente);

-- 1.2 Seccion en parametros de plantilla
ALTER TABLE public.parametro_plantilla
    ADD COLUMN IF NOT EXISTS seccion_id bigint;

-- 1.3 Timestamps faltantes en tablas versionadas
ALTER TABLE public.version_resultado
    ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE public.farmacia_receta_version
    ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE public.resultado_laboratorio
    ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE public.farmacia_entrega
    ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now();

ALTER TABLE public.asignacion_horario
    ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE public.turno_atencion
    ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE public.rrhh_ausencia
    ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- 1.4 created_by / updated_by en tablas transaccionales
DO $$
DECLARE
    t text;
    tablas text[] := ARRAY[
        'paciente','consulta','turno_atencion','solicitud','estudio_solicitado',
        'muestra','resultado_laboratorio','version_resultado','informe_imagen',
        'farmacia_receta','farmacia_receta_version','farmacia_entrega',
        'plantilla_examen','plantilla_examen_version','asignacion_horario',
        'rrhh_ausencia','usuario','estadistica_reporte_version','politica_conservacion'
    ];
BEGIN
    FOREACH t IN ARRAY tablas LOOP
        EXECUTE format(
            'ALTER TABLE public.%I
                 ADD COLUMN IF NOT EXISTS created_by bigint,
                 ADD COLUMN IF NOT EXISTS updated_by bigint', t);
        EXECUTE format(
            'ALTER TABLE public.%I
                 ADD CONSTRAINT %I FOREIGN KEY (created_by)
                 REFERENCES public.usuario(id) ON DELETE NO ACTION',
            t, 'fk_' || t || '_created_by');
        EXECUTE format(
            'ALTER TABLE public.%I
                 ADD CONSTRAINT %I FOREIGN KEY (updated_by)
                 REFERENCES public.usuario(id) ON DELETE NO ACTION',
            t, 'fk_' || t || '_updated_by');
    END LOOP;
END $$;


-- =====================================================================
-- 2. TABLAS OBLIGATORIAS QUE FALTABAN
-- =====================================================================

-- 2.1 Historial de estados de estudio (HU-N13 invalidacion, HU-N47 entrega parcial)
CREATE TABLE public.estudio_estado_historial (
    id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    estudio_id        bigint      NOT NULL REFERENCES public.estudio_solicitado(id) ON DELETE NO ACTION,
    estado_anterior   text,
    estado_nuevo      text        NOT NULL,
    motivo            text,
    usuario_id        bigint      REFERENCES public.usuario(id) ON DELETE NO ACTION,
    fecha_hora        timestamptz NOT NULL DEFAULT now(),
    created_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_eeh_estado_nuevo CHECK (estado_nuevo IN
        ('pendiente_muestra','resultado_en_preparacion','publicado','invalidado')),
    CONSTRAINT ck_eeh_motivo_invalidacion CHECK (
        estado_nuevo <> 'invalidado' OR (motivo IS NOT NULL AND length(btrim(motivo)) > 0))
);

-- 2.2 Secciones de plantilla de examen
CREATE TABLE public.seccion_plantilla (
    id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plantilla_version_id bigint  NOT NULL REFERENCES public.plantilla_examen_version(id) ON DELETE NO ACTION,
    nombre               text    NOT NULL,
    orden                integer NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_seccion_plantilla_orden UNIQUE (plantilla_version_id, orden)
);

ALTER TABLE public.parametro_plantilla
    ADD CONSTRAINT fk_parametro_seccion
    FOREIGN KEY (seccion_id) REFERENCES public.seccion_plantilla(id) ON DELETE NO ACTION;

-- 2.3 Emision oficial de documentos (copias, informes, recetas)
CREATE TABLE public.emision_documento (
    id                        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo                      text        NOT NULL,
    version_resultado_id      bigint      REFERENCES public.version_resultado(id) ON DELETE NO ACTION,
    informe_imagen_id         bigint      REFERENCES public.informe_imagen(id) ON DELETE NO ACTION,
    farmacia_receta_version_id bigint     REFERENCES public.farmacia_receta_version(id) ON DELETE NO ACTION,
    es_rectificacion          boolean     NOT NULL DEFAULT false,
    usuario_id                bigint      NOT NULL REFERENCES public.usuario(id) ON DELETE NO ACTION,
    fecha_hora                timestamptz NOT NULL DEFAULT now(),
    referencia_impresion      text,
    created_at                timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_emision_tipo CHECK (tipo IN ('copia_resultado','informe_imagen','receta')),
    CONSTRAINT ck_emision_una_fk CHECK (
        num_nonnulls(version_resultado_id, informe_imagen_id, farmacia_receta_version_id) = 1),
    CONSTRAINT ck_emision_tipo_coherente CHECK (
        (tipo = 'copia_resultado'  AND version_resultado_id IS NOT NULL) OR
        (tipo = 'informe_imagen'   AND informe_imagen_id IS NOT NULL) OR
        (tipo = 'receta'           AND farmacia_receta_version_id IS NOT NULL))
);

-- 2.4 Seguimiento de paciente (RF11)
CREATE TABLE public.seguimiento_paciente (
    id                    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    paciente_id           bigint NOT NULL REFERENCES public.paciente(id) ON DELETE NO ACTION,
    consulta_id           bigint REFERENCES public.consulta(id) ON DELETE NO ACTION,
    tipo                  text   NOT NULL,
    fecha_programada      date   NOT NULL,
    estado                text   NOT NULL DEFAULT 'pendiente',
    responsable_medico_id bigint REFERENCES public.medico(id) ON DELETE NO ACTION,
    observaciones         text,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    created_by            bigint REFERENCES public.usuario(id) ON DELETE NO ACTION,
    updated_by            bigint REFERENCES public.usuario(id) ON DELETE NO ACTION,
    CONSTRAINT ck_seguimiento_tipo   CHECK (tipo IN ('control','reevaluacion','resultado_pendiente','derivacion','otro')),
    CONSTRAINT ck_seguimiento_estado CHECK (estado IN ('pendiente','cumplido','no_asistio','cancelado'))
);

-- 2.5 Restauracion de respaldos
CREATE TABLE public.respaldo_restauracion (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    respaldo_id             bigint      NOT NULL REFERENCES public.respaldo_ejecucion(id) ON DELETE NO ACTION,
    usuario_id              bigint      NOT NULL REFERENCES public.usuario(id) ON DELETE NO ACTION,
    fecha_inicio            timestamptz NOT NULL,
    fecha_fin               timestamptz,
    datos_recuperados_hasta timestamptz,
    duracion                interval GENERATED ALWAYS AS (fecha_fin - fecha_inicio) STORED,
    estado                  text        NOT NULL,
    cumple_objetivos        boolean,
    detalle                 text,
    created_at              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_restauracion_estado CHECK (estado IN ('en_proceso','exitosa','incompleta','fallida')),
    CONSTRAINT ck_restauracion_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

-- 2.6 Evaluacion de jornada de RRHH
CREATE TABLE public.rrhh_jornada_evaluacion (
    id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trabajador_id        bigint NOT NULL REFERENCES public.trabajador(id) ON DELETE NO ACTION,
    fecha                date   NOT NULL,
    asignacion_horario_id bigint REFERENCES public.asignacion_horario(id) ON DELETE NO ACTION,
    estado               text   NOT NULL,
    motivo_pendiente     text,
    detalle_json         jsonb,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_jornada_trabajador_fecha UNIQUE (trabajador_id, fecha),
    CONSTRAINT ck_jornada_estado CHECK (estado IN ('calculada','pendiente_revision')),
    -- sin horario aplicable => pendiente_revision con motivo; nunca "injustificada"
    CONSTRAINT ck_jornada_pendiente CHECK (
        estado <> 'pendiente_revision' OR motivo_pendiente IS NOT NULL),
    CONSTRAINT ck_jornada_calculada CHECK (
        estado <> 'calculada' OR asignacion_horario_id IS NOT NULL)
);


-- =====================================================================
-- 3. CHECKS DE ESTADO Y CATALOGO QUE FALTABAN
--    (el script original dejo casi todos los "estado" como texto libre)
-- =====================================================================

ALTER TABLE public.paciente
    ADD CONSTRAINT ck_paciente_estado CHECK (estado IN ('activo','inactivo','fusionado')),
    ADD CONSTRAINT ck_paciente_sexo   CHECK (sexo IN ('M','F','otro','no_especificado')),
    -- si NO es sin_documento, el numero es obligatorio (faltaba el sentido inverso)
    ADD CONSTRAINT ck_paciente_doc_obligatorio CHECK (sin_documento OR numero_documento IS NOT NULL);

ALTER TABLE public.trabajador
    ADD CONSTRAINT ck_trabajador_estado CHECK (estado IN ('activo','inactivo')),
    ADD CONSTRAINT ck_trabajador_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio);

ALTER TABLE public.usuario
    ADD CONSTRAINT ck_usuario_estado CHECK (estado IN ('activo','inactivo','bloqueado'));

ALTER TABLE public.sesion_usuario
    ADD CONSTRAINT ck_sesion_estado CHECK (estado IN ('activa','expirada','revocada'));

ALTER TABLE public.auditoria_accion
    ADD CONSTRAINT ck_auditoria_accion CHECK (accion IN
        ('crear','modificar','publicar','rectificar','invalidar','anular',
         'consultar','acceder','exportar','importar'));

ALTER TABLE public.solicitud
    ADD CONSTRAINT ck_solicitud_prioridad CHECK (prioridad IN ('urgente','sin_prioridad')),
    -- si no hay FK al medico, debe existir el snapshot del nombre
    ADD CONSTRAINT ck_solicitud_medico CHECK (
        medico_solicitante_id IS NOT NULL OR medico_solicitante_nombre_snapshot IS NOT NULL);

ALTER TABLE public.estudio_solicitado
    ADD CONSTRAINT ck_estudio_estado CHECK (estado IN
        ('pendiente_muestra','resultado_en_preparacion','publicado','invalidado'));

ALTER TABLE public.version_resultado
    ADD CONSTRAINT ck_version_resultado_estado CHECK (estado IN ('borrador','publicado','rectificado')),
    ADD CONSTRAINT ck_version_resultado_publicacion CHECK (
        estado = 'borrador'
        OR (usuario_publicacion_id IS NOT NULL AND fecha_hora_publicacion IS NOT NULL));

ALTER TABLE public.informe_imagen
    ADD CONSTRAINT ck_informe_estado CHECK (estado IN ('borrador','publicado','rectificado')),
    ADD CONSTRAINT ck_informe_publicacion CHECK (
        estado = 'borrador'
        OR (usuario_publicacion_id IS NOT NULL AND fecha_hora_publicacion IS NOT NULL));

ALTER TABLE public.plantilla_examen_version
    ADD CONSTRAINT ck_plantilla_version_estado CHECK (estado IN ('borrador','activa','retirada'));

ALTER TABLE public.parametro_plantilla
    ADD CONSTRAINT ck_parametro_tipo CHECK (tipo_entrada IN
        ('entero','decimal','texto','cualitativo','rango')),
    ADD CONSTRAINT ck_parametro_rango CHECK (
        valor_minimo IS NULL OR valor_maximo IS NULL OR valor_minimo <= valor_maximo);

ALTER TABLE public.farmacia_receta
    ADD CONSTRAINT ck_receta_estado CHECK (estado IN ('vigente','rectificada','anulada','completada'));

ALTER TABLE public.farmacia_receta_version
    ADD CONSTRAINT ck_receta_version_estado CHECK (estado IN ('borrador','vigente','rectificada','anulada'));

ALTER TABLE public.farmacia_receta_detalle
    ADD CONSTRAINT ck_receta_detalle_cantidad CHECK (cantidad_prescrita > 0);

ALTER TABLE public.farmacia_entrega
    ADD CONSTRAINT ck_entrega_tipo CHECK (tipo_entrega IN ('completa','parcial')),
    ADD CONSTRAINT ck_entrega_receptor CHECK (tipo_receptor IN ('paciente','familiar','tercero_autorizado','personal_salud'));

ALTER TABLE public.farmacia_entrega_detalle
    ADD CONSTRAINT ck_entrega_detalle_cantidad CHECK (cantidad_entregada > 0);

ALTER TABLE public.rrhh_marcacion_asistencia
    ADD CONSTRAINT ck_marcacion_tipo CHECK (tipo IN ('entrada','salida'));

ALTER TABLE public.rrhh_ausencia
    ADD CONSTRAINT ck_ausencia_tipo CHECK (tipo IN
        ('vacaciones','baja_medica','dia_libre','permiso','falta_sin_justificar')),
    ADD CONSTRAINT ck_ausencia_fechas CHECK (fecha_fin >= fecha_inicio);

ALTER TABLE public.asignacion_horario
    ADD CONSTRAINT ck_asignacion_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio);

ALTER TABLE public.turno_atencion
    ADD CONSTRAINT ck_turno_estado CHECK (estado IN
        ('registrado','en_espera','llamado','en_consulta','atendido','cancelado','no_asistio'));

ALTER TABLE public.consulta
    ADD CONSTRAINT ck_consulta_estado CHECK (estado IN ('abierta','cerrada','anulada')),
    ADD CONSTRAINT ck_consulta_fechas CHECK (fecha_hora_fin IS NULL OR fecha_hora_fin >= fecha_hora_inicio);

ALTER TABLE public.evento_atencion
    ADD CONSTRAINT ck_evento_tipo CHECK (tipo_evento IN
        ('registrado','en_espera','llamado','en_consulta','atendido','cancelado'));

ALTER TABLE public.ia_generacion
    ADD CONSTRAINT ck_ia_estado_revision CHECK (estado_revision IN
        ('pendiente_revision','confirmado','rechazado')),
    ADD CONSTRAINT ck_ia_revision_completa CHECK (
        estado_revision = 'pendiente_revision'
        OR (usuario_revisor_id IS NOT NULL AND fecha_revision IS NOT NULL));

ALTER TABLE public.transcripcion
    ADD CONSTRAINT ck_transcripcion_estado CHECK (estado IN ('pendiente','procesando','completada','fallida'));

ALTER TABLE public.importacion_archivo
    ADD CONSTRAINT ck_importacion_estado CHECK (estado IN
        ('cargado','validado','confirmado','rechazado','parcial')),
    ADD CONSTRAINT ck_importacion_totales CHECK (
        total_registros IS NULL OR total_registros >= COALESCE(total_validos,0) + COALESCE(total_rechazados,0));

ALTER TABLE public.importacion_detalle
    ADD CONSTRAINT ck_importacion_detalle_estado CHECK (estado IN
        ('valido','rechazado','pendiente','aplicado')),
    ADD CONSTRAINT ck_importacion_detalle_motivo CHECK (
        estado <> 'rechazado' OR motivo_error IS NOT NULL);

ALTER TABLE public.respaldo_ejecucion
    ADD CONSTRAINT ck_respaldo_estado CHECK (estado IN ('en_proceso','exitoso','fallido'));

ALTER TABLE public.estadistica_reporte_version
    ADD CONSTRAINT ck_reporte_version_estado CHECK (estado IN ('borrador','cerrado','anulado')),
    ADD CONSTRAINT ck_reporte_version_periodo CHECK (periodo_fin >= periodo_inicio);

ALTER TABLE public.archivo_imagen
    ADD CONSTRAINT ck_archivo_retiro CHECK (activo OR motivo_retiro IS NOT NULL),
    ADD CONSTRAINT ck_archivo_tamano CHECK (tamano_bytes > 0);


-- =====================================================================
-- 4. UNIQUE / IDEMPOTENCIA / UNA SOLA VERSION VIGENTE
-- =====================================================================

-- 4.1 Una sola cuenta activa por trabajador
CREATE UNIQUE INDEX uq_usuario_trabajador_activo
    ON public.usuario (trabajador_id) WHERE estado = 'activo';

-- 4.2 Maximo una version publicada vigente por resultado / informe / receta
CREATE UNIQUE INDEX uq_version_resultado_publicada
    ON public.version_resultado (resultado_id) WHERE estado = 'publicado';

CREATE UNIQUE INDEX uq_informe_imagen_publicado
    ON public.informe_imagen (estudio_id) WHERE estado = 'publicado';

CREATE UNIQUE INDEX uq_receta_version_vigente
    ON public.farmacia_receta_version (receta_id) WHERE estado = 'vigente';

-- 4.3 Claves de idempotencia (evitan duplicados por reintento)
CREATE UNIQUE INDEX uq_solicitud_idempotencia
    ON public.solicitud (clave_idempotencia) WHERE clave_idempotencia IS NOT NULL;

CREATE UNIQUE INDEX uq_entrega_idempotencia
    ON public.farmacia_entrega (clave_idempotencia) WHERE clave_idempotencia IS NOT NULL;

CREATE UNIQUE INDEX uq_importacion_hash
    ON public.importacion_archivo (tipo_importacion, hash_sha256);

CREATE UNIQUE INDEX uq_importacion_detalle_clave
    ON public.importacion_detalle (importacion_id, numero_fila);

-- 4.4 Unicidad de valores por version de resultado
CREATE UNIQUE INDEX uq_detalle_valor_version_param
    ON public.detalle_valor_resultado (version_resultado_id, parametro_id);

-- 4.5 Un solo diagnostico principal por consulta
CREATE UNIQUE INDEX uq_consulta_diagnostico_principal
    ON public.consulta_diagnostico (consulta_id)
    WHERE principal;

-- 4.6 Codigo de parametro unico dentro de su version de plantilla
CREATE UNIQUE INDEX uq_parametro_codigo_version
    ON public.parametro_plantilla (plantilla_version_id, codigo);


-- =====================================================================
-- 5. INDICES DE BUSQUEDA (seccion 18 del prompt)
-- =====================================================================

CREATE INDEX ix_paciente_nombre           ON public.paciente (lower(nombre_completo));
CREATE INDEX ix_paciente_documento        ON public.paciente (numero_documento);
CREATE INDEX ix_paciente_estab            ON public.paciente (establecimiento_procedencia_id);

CREATE INDEX ix_consulta_paciente_fecha   ON public.consulta (paciente_id, fecha_hora_inicio DESC);
CREATE INDEX ix_consulta_medico_fecha     ON public.consulta (medico_id, fecha_hora_inicio DESC);
CREATE INDEX ix_turno_fecha_estado        ON public.turno_atencion (fecha, estado);
CREATE INDEX ix_evento_atencion_turno     ON public.evento_atencion (turno_id, fecha_hora);

CREATE INDEX ix_solicitud_paciente_fecha  ON public.solicitud (paciente_id, fecha_solicitud DESC);
CREATE INDEX ix_solicitud_referencia      ON public.solicitud (referencia);

CREATE INDEX ix_estudio_servicio_estado   ON public.estudio_solicitado (servicio_id, estado);
CREATE INDEX ix_estudio_solicitud         ON public.estudio_solicitado (solicitud_id);
CREATE INDEX ix_estudio_paciente          ON public.estudio_solicitado (paciente_id);
CREATE INDEX ix_estudio_pendientes        ON public.estudio_solicitado (servicio_id, created_at)
    WHERE estado IN ('pendiente_muestra','resultado_en_preparacion');
CREATE INDEX ix_estudio_historial         ON public.estudio_estado_historial (estudio_id, fecha_hora DESC);

CREATE INDEX ix_muestra_paciente_fecha    ON public.muestra (paciente_id, fecha_toma_real DESC);
CREATE INDEX ix_muestra_referencia        ON public.muestra (referencia_muestra);
CREATE INDEX ix_muestra_estudio_estudio   ON public.muestra_estudio (estudio_id);

CREATE INDEX ix_version_resultado_res     ON public.version_resultado (resultado_id, numero_version DESC);
CREATE INDEX ix_detalle_valor_version     ON public.detalle_valor_resultado (version_resultado_id);

CREATE INDEX ix_informe_estudio           ON public.informe_imagen (estudio_id, numero_version DESC);
CREATE INDEX ix_archivo_informe           ON public.archivo_imagen (informe_id) WHERE activo;
CREATE INDEX ix_archivo_hash              ON public.archivo_imagen (hash_sha256);

CREATE INDEX ix_receta_paciente_fecha     ON public.farmacia_receta (paciente_id, fecha_emision DESC);
CREATE INDEX ix_receta_estado             ON public.farmacia_receta (estado);
CREATE INDEX ix_receta_version_receta     ON public.farmacia_receta_version (receta_id, numero_version DESC);
CREATE INDEX ix_receta_detalle_version    ON public.farmacia_receta_detalle (receta_version_id);
CREATE INDEX ix_entrega_receta_version    ON public.farmacia_entrega (receta_version_id, fecha_hora DESC);
CREATE INDEX ix_entrega_detalle_entrega   ON public.farmacia_entrega_detalle (entrega_id);
CREATE INDEX ix_entrega_detalle_receta_d  ON public.farmacia_entrega_detalle (receta_detalle_id);

CREATE INDEX ix_marcacion_trab_fecha      ON public.rrhh_marcacion_asistencia (trabajador_id, fecha_hora);
CREATE INDEX ix_ausencia_trab_periodo     ON public.rrhh_ausencia (trabajador_id, fecha_inicio, fecha_fin);
CREATE INDEX ix_asignacion_trab_periodo   ON public.asignacion_horario (trabajador_id, fecha_inicio, fecha_fin);
CREATE INDEX ix_jornada_trab_fecha        ON public.rrhh_jornada_evaluacion (trabajador_id, fecha DESC);

CREATE INDEX ix_auditoria_usuario_fecha   ON public.auditoria_accion (usuario_id, fecha_hora DESC);
CREATE INDEX ix_auditoria_entidad_ref     ON public.auditoria_accion (entidad_afectada, referencia_registro);

CREATE INDEX ix_ia_fuente_generacion      ON public.ia_fuente (generacion_id);
CREATE INDEX ix_ia_generacion_paciente    ON public.ia_generacion (paciente_id, fecha_generacion DESC);
CREATE INDEX ix_ia_pendientes             ON public.ia_generacion (estado_revision)
    WHERE estado_revision = 'pendiente_revision';

CREATE INDEX ix_importacion_periodo       ON public.importacion_archivo (tipo_importacion, periodo_inicio, periodo_fin);
CREATE INDEX ix_emision_documento_fecha   ON public.emision_documento (tipo, fecha_hora DESC);
CREATE INDEX ix_seguimiento_pendiente     ON public.seguimiento_paciente (fecha_programada)
    WHERE estado = 'pendiente';
CREATE INDEX ix_sesion_usuario_activa     ON public.sesion_usuario (usuario_id) WHERE estado = 'activa';


-- =====================================================================
-- 6. FUNCIONES Y TRIGGERS (seccion 17 del prompt)
-- =====================================================================

-- 6.1 updated_at automatico en TODAS las tablas que tengan la columna
--     (se eliminan los 3 triggers puntuales que ya traia el script original
--      para no dejar dos triggers duplicados sobre la misma tabla)
DROP TRIGGER IF EXISTS actualizar_consulta_updated_at ON public.consulta;
DROP TRIGGER IF EXISTS actualizar_paciente_updated_at  ON public.paciente;
DROP TRIGGER IF EXISTS actualizar_usuario_updated_at   ON public.usuario;

DO $$
DECLARE r record;
BEGIN
    FOR r IN
        SELECT c.table_name
          FROM information_schema.columns c
          JOIN information_schema.tables t
            ON t.table_schema = c.table_schema AND t.table_name = c.table_name
         WHERE c.table_schema = 'public'
           AND c.column_name  = 'updated_at'
           AND t.table_type   = 'BASE TABLE'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%s_updated_at ON public.%I', r.table_name, r.table_name);
        EXECUTE format('CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON public.%I
                        FOR EACH ROW EXECUTE FUNCTION public.actualizar_updated_at()',
                        r.table_name, r.table_name);
    END LOOP;
END $$;


-- 6.2 Auditoria inmutable
CREATE OR REPLACE FUNCTION public.auditoria_inmutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'auditoria_accion es inmutable: no se permite % ', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auditoria_inmutable
    BEFORE UPDATE OR DELETE ON public.auditoria_accion
    FOR EACH ROW EXECUTE FUNCTION public.auditoria_inmutable();


-- 6.3 Prohibicion de borrado fisico en informacion clinica
CREATE OR REPLACE FUNCTION public.prohibir_borrado() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION
        'No se permite borrado fisico en %. Use estado/historial.', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t text;
    tablas text[] := ARRAY[
        'paciente','consulta','solicitud','estudio_solicitado','muestra',
        'resultado_laboratorio','version_resultado','detalle_valor_resultado',
        'informe_imagen','archivo_imagen','farmacia_receta','farmacia_receta_version',
        'farmacia_receta_detalle','farmacia_entrega','farmacia_entrega_detalle',
        'usuario','trabajador','emision_documento','estudio_estado_historial',
        'estadistica_reporte_version'
    ];
BEGIN
    FOREACH t IN ARRAY tablas LOOP
        EXECUTE format('CREATE TRIGGER trg_%s_no_delete BEFORE DELETE ON public.%I
                        FOR EACH ROW EXECUTE FUNCTION public.prohibir_borrado()', t, t);
    END LOOP;
END $$;


-- 6.4 Inmutabilidad de versiones clinicas publicadas
--     Unica transicion permitida: publicado -> rectificado (solo el estado),
--     y solo si ya existe una version posterior publicada.
CREATE OR REPLACE FUNCTION public.proteger_version_publicada() RETURNS trigger AS $$
DECLARE
    existe_posterior boolean;
BEGIN
    IF OLD.estado <> 'publicado' THEN
        RETURN NEW;  -- borradores si se pueden editar
    END IF;

    IF NEW.estado <> 'rectificado' THEN
        RAISE EXCEPTION 'Una version publicada no puede modificarse (%). Genere una nueva version.',
            TG_TABLE_NAME;
    END IF;

    -- Nada mas que el estado puede cambiar
    IF TG_TABLE_NAME = 'version_resultado' THEN
        IF NEW.resultado_id IS DISTINCT FROM OLD.resultado_id
           OR NEW.numero_version IS DISTINCT FROM OLD.numero_version
           OR NEW.usuario_publicacion_id IS DISTINCT FROM OLD.usuario_publicacion_id
           OR NEW.fecha_hora_publicacion IS DISTINCT FROM OLD.fecha_hora_publicacion THEN
            RAISE EXCEPTION 'Solo se permite cambiar el estado a rectificado.';
        END IF;
        SELECT EXISTS (SELECT 1 FROM public.version_resultado v
                        WHERE v.resultado_id = OLD.resultado_id
                          AND v.numero_version > OLD.numero_version
                          AND v.estado = 'publicado')
          INTO existe_posterior;

    ELSIF TG_TABLE_NAME = 'informe_imagen' THEN
        IF NEW.estudio_id IS DISTINCT FROM OLD.estudio_id
           OR NEW.numero_version IS DISTINCT FROM OLD.numero_version
           OR NEW.descripcion_texto IS DISTINCT FROM OLD.descripcion_texto
           OR NEW.usuario_publicacion_id IS DISTINCT FROM OLD.usuario_publicacion_id
           OR NEW.fecha_hora_publicacion IS DISTINCT FROM OLD.fecha_hora_publicacion THEN
            RAISE EXCEPTION 'Solo se permite cambiar el estado a rectificado.';
        END IF;
        SELECT EXISTS (SELECT 1 FROM public.informe_imagen i
                        WHERE i.estudio_id = OLD.estudio_id
                          AND i.numero_version > OLD.numero_version
                          AND i.estado = 'publicado')
          INTO existe_posterior;
    ELSE
        existe_posterior := false;
    END IF;

    IF NOT existe_posterior THEN
        RAISE EXCEPTION 'No se puede rectificar sin una version posterior publicada.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_version_resultado_inmutable
    BEFORE UPDATE ON public.version_resultado
    FOR EACH ROW EXECUTE FUNCTION public.proteger_version_publicada();

CREATE TRIGGER trg_informe_imagen_inmutable
    BEFORE UPDATE ON public.informe_imagen
    FOR EACH ROW EXECUTE FUNCTION public.proteger_version_publicada();

-- Los valores de una version publicada tampoco se tocan
CREATE OR REPLACE FUNCTION public.proteger_valores_publicados() RETURNS trigger AS $$
DECLARE v_estado text;
BEGIN
    SELECT estado INTO v_estado
      FROM public.version_resultado
     WHERE id = COALESCE(NEW.version_resultado_id, OLD.version_resultado_id);

    IF v_estado IN ('publicado','rectificado') THEN
        RAISE EXCEPTION 'No se pueden alterar valores de una version ya publicada.';
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_detalle_valor_protegido
    BEFORE INSERT OR UPDATE ON public.detalle_valor_resultado
    FOR EACH ROW EXECUTE FUNCTION public.proteger_valores_publicados();


-- 6.5 Coherencia parametro <-> version de plantilla, y tipo de valor
CREATE OR REPLACE FUNCTION public.validar_detalle_valor() RETURNS trigger AS $$
DECLARE
    v_plantilla_resultado bigint;
    v_plantilla_param     bigint;
    v_tipo                text;
    v_llenos              integer;
BEGIN
    SELECT r.plantilla_version_id INTO v_plantilla_resultado
      FROM public.version_resultado vr
      JOIN public.resultado_laboratorio r ON r.id = vr.resultado_id
     WHERE vr.id = NEW.version_resultado_id;

    SELECT p.plantilla_version_id, p.tipo_entrada INTO v_plantilla_param, v_tipo
      FROM public.parametro_plantilla p
     WHERE p.id = NEW.parametro_id;

    IF v_plantilla_param IS DISTINCT FROM v_plantilla_resultado THEN
        RAISE EXCEPTION
          'El parametro % no pertenece a la version de plantilla usada por el resultado.',
          NEW.parametro_id;
    END IF;

    v_llenos := num_nonnulls(NEW.valor_entero, NEW.valor_decimal,
                             NEW.valor_texto, NEW.valor_cualitativo);

    -- Un campo vacio queda PENDIENTE: no se convierte en 0 ni en "normal"
    IF v_llenos = 0 THEN
        RETURN NEW;
    END IF;

    IF v_llenos > 1 THEN
        RAISE EXCEPTION 'Solo puede informarse un tipo de valor por parametro.';
    END IF;

    IF (v_tipo = 'entero'      AND NEW.valor_entero      IS NULL)
    OR (v_tipo = 'decimal'     AND NEW.valor_decimal     IS NULL)
    OR (v_tipo IN ('texto','rango') AND NEW.valor_texto  IS NULL)
    OR (v_tipo = 'cualitativo' AND NEW.valor_cualitativo IS NULL) THEN
        RAISE EXCEPTION 'El valor no corresponde al tipo de entrada "%" del parametro.', v_tipo;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_detalle_valor
    BEFORE INSERT OR UPDATE ON public.detalle_valor_resultado
    FOR EACH ROW EXECUTE FUNCTION public.validar_detalle_valor();

-- Seccion del parametro debe ser de la misma version de plantilla
CREATE OR REPLACE FUNCTION public.validar_seccion_parametro() RETURNS trigger AS $$
DECLARE v_pv bigint;
BEGIN
    IF NEW.seccion_id IS NULL THEN RETURN NEW; END IF;
    SELECT plantilla_version_id INTO v_pv FROM public.seccion_plantilla WHERE id = NEW.seccion_id;
    IF v_pv IS DISTINCT FROM NEW.plantilla_version_id THEN
        RAISE EXCEPTION 'La seccion pertenece a otra version de plantilla.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_seccion_parametro
    BEFORE INSERT OR UPDATE ON public.parametro_plantilla
    FOR EACH ROW EXECUTE FUNCTION public.validar_seccion_parametro();


-- 6.6 Una muestra no puede asociarse a estudios de pacientes distintos
CREATE OR REPLACE FUNCTION public.validar_muestra_estudio() RETURNS trigger AS $$
DECLARE
    v_pac_muestra bigint;
    v_pac_estudio bigint;
BEGIN
    SELECT paciente_id INTO v_pac_muestra FROM public.muestra          WHERE id = NEW.muestra_id;
    SELECT paciente_id INTO v_pac_estudio FROM public.estudio_solicitado WHERE id = NEW.estudio_id;

    IF v_pac_muestra IS DISTINCT FROM v_pac_estudio THEN
        RAISE EXCEPTION
          'La muestra pertenece al paciente % y el estudio al paciente %.',
          v_pac_muestra, v_pac_estudio;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_muestra_estudio
    BEFORE INSERT OR UPDATE ON public.muestra_estudio
    FOR EACH ROW EXECUTE FUNCTION public.validar_muestra_estudio();


-- 6.7 Farmacia: saldo prescrito y recetas anuladas
CREATE OR REPLACE FUNCTION public.validar_entrega_detalle() RETURNS trigger AS $$
DECLARE
    v_prescrita   numeric;
    v_entregada   numeric;
    v_estado_ver  text;
    v_estado_rec  text;
    v_ver_detalle bigint;
    v_ver_entrega bigint;
BEGIN
    SELECT d.cantidad_prescrita, d.receta_version_id
      INTO v_prescrita, v_ver_detalle
      FROM public.farmacia_receta_detalle d
     WHERE d.id = NEW.receta_detalle_id;

    SELECT e.receta_version_id INTO v_ver_entrega
      FROM public.farmacia_entrega e WHERE e.id = NEW.entrega_id;

    IF v_ver_detalle IS DISTINCT FROM v_ver_entrega THEN
        RAISE EXCEPTION 'El detalle pertenece a otra version de receta.';
    END IF;

    SELECT v.estado, r.estado INTO v_estado_ver, v_estado_rec
      FROM public.farmacia_receta_version v
      JOIN public.farmacia_receta r ON r.id = v.receta_id
     WHERE v.id = v_ver_entrega;

    IF v_estado_rec = 'anulada' OR v_estado_ver IN ('anulada','rectificada') THEN
        RAISE EXCEPTION 'No se aceptan entregas sobre una receta anulada o rectificada.';
    END IF;

    SELECT COALESCE(sum(ed.cantidad_entregada), 0) INTO v_entregada
      FROM public.farmacia_entrega_detalle ed
     WHERE ed.receta_detalle_id = NEW.receta_detalle_id
       AND ed.id IS DISTINCT FROM NEW.id;

    IF v_entregada + NEW.cantidad_entregada > v_prescrita THEN
        RAISE EXCEPTION
          'Cantidad excede el saldo: prescrito %, ya entregado %, solicitado %.',
          v_prescrita, v_entregada, NEW.cantidad_entregada;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_entrega_detalle
    BEFORE INSERT OR UPDATE ON public.farmacia_entrega_detalle
    FOR EACH ROW EXECUTE FUNCTION public.validar_entrega_detalle();


-- 6.8 Historial automatico de estados de estudio
CREATE OR REPLACE FUNCTION public.registrar_estado_estudio() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO public.estudio_estado_historial
            (estudio_id, estado_anterior, estado_nuevo, motivo, usuario_id)
        VALUES (NEW.id, NULL, NEW.estado, NULL, NEW.created_by);
    ELSIF NEW.estado IS DISTINCT FROM OLD.estado THEN
        IF NEW.estado = 'invalidado' AND NEW.motivo_invalidacion IS NULL THEN
            RAISE EXCEPTION 'Invalidar un estudio requiere motivo.';
        END IF;
        INSERT INTO public.estudio_estado_historial
            (estudio_id, estado_anterior, estado_nuevo, motivo, usuario_id)
        VALUES (NEW.id, OLD.estado, NEW.estado, NEW.motivo_invalidacion, NEW.updated_by);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

ALTER TABLE public.estudio_solicitado
    ADD COLUMN IF NOT EXISTS motivo_invalidacion text;

ALTER TABLE public.estudio_solicitado
    ADD CONSTRAINT ck_estudio_motivo_invalidacion CHECK (
        estado <> 'invalidado' OR motivo_invalidacion IS NOT NULL);

CREATE TRIGGER trg_registrar_estado_estudio
    AFTER INSERT OR UPDATE ON public.estudio_solicitado
    FOR EACH ROW EXECUTE FUNCTION public.registrar_estado_estudio();


-- 6.9 Solo se emiten documentos de versiones publicadas / vigentes
CREATE OR REPLACE FUNCTION public.validar_emision_documento() RETURNS trigger AS $$
DECLARE v_estado text;
BEGIN
    IF NEW.version_resultado_id IS NOT NULL THEN
        SELECT estado INTO v_estado FROM public.version_resultado WHERE id = NEW.version_resultado_id;
        IF v_estado <> 'publicado' THEN
            RAISE EXCEPTION 'Solo se emiten copias de resultados publicados (estado actual: %).', v_estado;
        END IF;
    ELSIF NEW.informe_imagen_id IS NOT NULL THEN
        SELECT estado INTO v_estado FROM public.informe_imagen WHERE id = NEW.informe_imagen_id;
        IF v_estado <> 'publicado' THEN
            RAISE EXCEPTION 'Solo se emiten informes publicados (estado actual: %).', v_estado;
        END IF;
    ELSE
        SELECT estado INTO v_estado FROM public.farmacia_receta_version WHERE id = NEW.farmacia_receta_version_id;
        IF v_estado <> 'vigente' THEN
            RAISE EXCEPTION 'Solo se emiten recetas vigentes (estado actual: %).', v_estado;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_emision_documento
    BEFORE INSERT ON public.emision_documento
    FOR EACH ROW EXECUTE FUNCTION public.validar_emision_documento();


-- 6.10 Sesion de usuario: no revivir sesiones cerradas
CREATE OR REPLACE FUNCTION public.validar_sesion() RETURNS trigger AS $$
BEGIN
    IF OLD.estado IN ('expirada','revocada') AND NEW.estado = 'activa' THEN
        RAISE EXCEPTION 'Una sesion cerrada no puede reactivarse.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_sesion
    BEFORE UPDATE ON public.sesion_usuario
    FOR EACH ROW EXECUTE FUNCTION public.validar_sesion();


-- 6.11 Solapamientos de horario: se REGISTRAN, no se bloquean (ajuste del prompt)
CREATE OR REPLACE FUNCTION public.detectar_solapamientos_horario(
    p_fecha_desde date DEFAULT NULL,
    p_fecha_hasta date DEFAULT NULL)
RETURNS TABLE (
    trabajador_id   bigint,
    asignacion_a_id bigint,
    asignacion_b_id bigint,
    horario_a_id    bigint,
    horario_b_id    bigint,
    desde           date,
    hasta           date
) AS $$
    SELECT a.trabajador_id,
           a.id, b.id,
           a.horario_id, b.horario_id,
           GREATEST(a.fecha_inicio, b.fecha_inicio),
           LEAST(COALESCE(a.fecha_fin, DATE '9999-12-31'),
                 COALESCE(b.fecha_fin, DATE '9999-12-31'))
      FROM public.asignacion_horario a
      JOIN public.asignacion_horario b
        ON a.trabajador_id = b.trabajador_id
       AND a.id < b.id
       AND a.fecha_inicio <= COALESCE(b.fecha_fin, DATE '9999-12-31')
       AND b.fecha_inicio <= COALESCE(a.fecha_fin, DATE '9999-12-31')
     WHERE (p_fecha_desde IS NULL OR COALESCE(a.fecha_fin, DATE '9999-12-31') >= p_fecha_desde)
       AND (p_fecha_hasta IS NULL OR a.fecha_inicio <= p_fecha_hasta);
$$ LANGUAGE sql STABLE;

-- Ausencias solapadas: tambien se señalan, no se bloquean
CREATE OR REPLACE VIEW public.vista_ausencias_solapadas AS
SELECT a.trabajador_id, a.id AS ausencia_a_id, b.id AS ausencia_b_id,
       a.tipo AS tipo_a, b.tipo AS tipo_b,
       GREATEST(a.fecha_inicio, b.fecha_inicio) AS desde,
       LEAST(a.fecha_fin, b.fecha_fin)          AS hasta
  FROM public.rrhh_ausencia a
  JOIN public.rrhh_ausencia b
    ON a.trabajador_id = b.trabajador_id
   AND a.id < b.id
   AND a.fecha_inicio <= b.fecha_fin
   AND b.fecha_inicio <= a.fecha_fin;


-- =====================================================================
-- 7. VISTAS UTILES
-- =====================================================================

-- 7.1 Estado de solicitud: completa/parcial, con publicados y pendientes separados.
--     Los pendientes NO exponen valores: solo se listan como pendientes.
-- Se elimina primero: la version anterior de esta vista (la del script original)
-- tiene columnas en otro orden/cantidad, y PostgreSQL no permite que
-- CREATE OR REPLACE VIEW reordene o inserte columnas en el medio.
DROP VIEW IF EXISTS public.vista_solicitud_estado;

CREATE VIEW public.vista_solicitud_estado AS
SELECT s.id                          AS solicitud_id,
       s.referencia,
       s.paciente_id,
       s.prioridad,
       s.fecha_solicitud,
       count(e.id)                                                   AS total_estudios,
       count(e.id) FILTER (WHERE e.estado = 'publicado')             AS total_publicados,
       count(e.id) FILTER (WHERE e.estado = 'invalidado')            AS total_invalidados,
       CASE
           WHEN count(e.id) = 0 THEN 'sin_estudios'
           WHEN count(e.id) FILTER (WHERE e.estado IN ('publicado','invalidado')) = count(e.id)
                THEN 'completa'
           WHEN count(e.id) FILTER (WHERE e.estado = 'publicado') > 0
                THEN 'parcial'
           ELSE 'pendiente'
       END                                                           AS estado_solicitud,
       array_agg(e.referencia) FILTER (WHERE e.estado = 'publicado') AS estudios_publicados,
       array_agg(e.referencia) FILTER (
           WHERE e.estado IN ('pendiente_muestra','resultado_en_preparacion'))
                                                                     AS estudios_pendientes
  FROM public.solicitud s
  LEFT JOIN public.estudio_solicitado e ON e.solicitud_id = s.id
 GROUP BY s.id;

-- 7.2 Saldo pendiente por medicamento prescrito
CREATE OR REPLACE VIEW public.vista_receta_saldo AS
SELECT d.id                AS receta_detalle_id,
       v.receta_id,
       d.receta_version_id,
       d.medicamento_id,
       d.nombre_medicamento_snapshot,
       d.cantidad_prescrita,
       COALESCE(sum(ed.cantidad_entregada), 0)                       AS cantidad_entregada,
       d.cantidad_prescrita - COALESCE(sum(ed.cantidad_entregada), 0) AS cantidad_pendiente
  FROM public.farmacia_receta_detalle d
  JOIN public.farmacia_receta_version v ON v.id = d.receta_version_id
  LEFT JOIN public.farmacia_entrega_detalle ed ON ed.receta_detalle_id = d.id
 GROUP BY d.id, v.receta_id, d.receta_version_id, d.medicamento_id,
          d.nombre_medicamento_snapshot, d.cantidad_prescrita;

-- 7.3 Resultado vigente por estudio
CREATE OR REPLACE VIEW public.vista_resultado_vigente AS
SELECT r.estudio_id, r.id AS resultado_id, vr.id AS version_resultado_id,
       vr.numero_version, vr.fecha_hora_publicacion, vr.usuario_publicacion_id
  FROM public.resultado_laboratorio r
  JOIN public.version_resultado vr ON vr.resultado_id = r.id
 WHERE vr.estado = 'publicado';

-- 7.4 Tiempos de espera y atencion
CREATE OR REPLACE VIEW public.vista_tiempos_atencion AS
SELECT t.id AS turno_id, t.paciente_id, t.fecha,
       min(e.fecha_hora) FILTER (WHERE e.tipo_evento = 'registrado')  AS hora_registro,
       min(e.fecha_hora) FILTER (WHERE e.tipo_evento = 'en_consulta') AS hora_inicio_atencion,
       max(e.fecha_hora) FILTER (WHERE e.tipo_evento = 'atendido')    AS hora_fin_atencion,
       min(e.fecha_hora) FILTER (WHERE e.tipo_evento = 'en_consulta')
         - min(e.fecha_hora) FILTER (WHERE e.tipo_evento = 'registrado')  AS tiempo_espera,
       max(e.fecha_hora) FILTER (WHERE e.tipo_evento = 'atendido')
         - min(e.fecha_hora) FILTER (WHERE e.tipo_evento = 'en_consulta') AS tiempo_atencion
  FROM public.turno_atencion t
  LEFT JOIN public.evento_atencion e ON e.turno_id = t.id
 GROUP BY t.id;


-- =====================================================================
-- 8. DATOS INICIALES FALTANTES
-- =====================================================================

INSERT INTO public.servicio (codigo, nombre, tipo, activo) VALUES
    ('LAB',  'Laboratorio', 'clinico',       true),
    ('IMG',  'Imagenologia','clinico',       true),
    ('FAR',  'Farmacia',    'apoyo',         true),
    ('CON',  'Consultorio', 'clinico',       true),
    ('RRHH', 'Recursos Humanos','administrativo', true),
    ('EST',  'Estadistica', 'administrativo',true)
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO public.establecimiento (codigo, nombre, tipo, activo) VALUES
    ('HSB', 'Hospital Sarcobamba', 'propio', true)
ON CONFLICT (codigo) DO NOTHING;

-- rol_permiso: un rol por usuario, los permisos se derivan del rol
INSERT INTO public.rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id
  FROM public.rol r
  CROSS JOIN public.permiso p
 WHERE (r.codigo = 'medico'        AND p.codigo IN ('crear','modificar','consultar','acceder','publicar','rectificar'))
    OR (r.codigo = 'laboratorio'   AND p.codigo IN ('crear','modificar','publicar','rectificar','invalidar','consultar','acceder'))
    OR (r.codigo = 'imagenes'      AND p.codigo IN ('crear','modificar','publicar','rectificar','invalidar','consultar','acceder'))
    OR (r.codigo = 'farmacia'      AND p.codigo IN ('crear','modificar','anular','consultar','acceder'))
    OR (r.codigo = 'rrhh'          AND p.codigo IN ('crear','modificar','importar','exportar','consultar','acceder'))
    OR (r.codigo = 'estadistica'   AND p.codigo IN ('crear','exportar','importar','consultar','acceder'))
    OR (r.codigo = 'accesos'       AND p.codigo IN ('crear','modificar','consultar','acceder'))
    OR (r.codigo = 'direccion'     AND p.codigo IN ('consultar','acceder','exportar'))
    OR (r.codigo = 'administracion'AND p.codigo IN ('crear','modificar','consultar','acceder','exportar'))
ON CONFLICT DO NOTHING;


-- =====================================================================
-- 9. REGLAS QUE NO PUEDEN GARANTIZARSE SOLO EN SQL
--    (quedan obligatoriamente en la capa de aplicacion)
-- =====================================================================
--
--  1. Auditoria de lecturas (acciones 'consultar' / 'acceder'): un trigger de
--     tabla NO detecta SELECT. Debe registrarlo la aplicacion o pgaudit.
--  2. Hash de contrasena y de tokens de sesion: la BD solo almacena el hash;
--     el algoritmo y el salt son responsabilidad de la aplicacion.
--  3. Invalidacion de sesiones al cambiar el rol o los permisos de un usuario.
--  4. Calculo y clasificacion de jornadas de RRHH (rrhh_jornada_evaluacion):
--     la BD guarda el resultado y su explicacion, no ejecuta el calculo.
--  5. Previsualizacion "validos vs rechazados" antes de confirmar una
--     importacion: es un flujo de UI; la BD solo impide reimportar el mismo
--     archivo (UNIQUE por hash) y conserva la fila de origen.
--  6. Decision de borrado tras vencer una politica de conservacion: nunca
--     automatica, requiere accion humana registrada.
--  7. Que la IA no se convierta en informacion clinica definitiva: la BD
--     exige estado_revision + revisor, pero el flujo de confirmacion es de
--     la aplicacion.
--  8. Asignacion de created_by / updated_by: la aplicacion debe informar el
--     usuario de sesion en cada escritura.
--  9. Solapamientos de horarios y ausencias: por decision de diseño NO se
--     bloquean; la aplicacion debe mostrar detectar_solapamientos_horario()
--     y vista_ausencias_solapadas antes del calculo definitivo.
-- 10. Generacion de referencias legibles (solicitud.referencia,
--     estudio_solicitado.referencia, muestra.referencia_muestra) y de
--     claves de idempotencia: las genera la aplicacion; la BD solo
--     garantiza su unicidad.
-- =====================================================================
-- =====================================================================
-- MIGRACION: eliminar modulos RRHH / Estadistica / Importacion / Respaldo
-- y simplificar respaldo_ejecucion.
-- Se ejecuta UNA sola vez sobre el esquema ya creado.
-- No toca: paciente, consulta, solicitud, laboratorio, imagenes,
-- farmacia, IA, trabajador, trabajador_estado_historial, medico, usuario.
-- =====================================================================


-- =====================================================================
-- 1. ELIMINAR TABLAS (con CASCADE: se llevan indices, triggers, FKs y
--    vistas que dependan de ellas)
-- =====================================================================

DROP TABLE IF EXISTS
    public.horario,
    public.horario_jornada,
    public.asignacion_horario,
    public.rrhh_marcacion_asistencia,
    public.rrhh_ausencia,
    public.rrhh_feriado,
    public.rrhh_jornada_evaluacion,
    public.estadistica_indicador,
    public.estadistica_regla_correspondencia,
    public.estadistica_reporte,
    public.estadistica_reporte_version,
    public.estadistica_reporte_fuente,
    public.importacion_archivo,
    public.importacion_detalle,
    public.politica_conservacion,
    public.respaldo_restauracion
    CASCADE;


-- =====================================================================
-- 2. FUNCIONES HUERFANAS
--    (no se caen solas con el DROP TABLE porque una funcion no crea una
--    dependencia de catalogo sobre las tablas que solo usa en su cuerpo;
--    la vista vista_ausencias_solapadas si dependia de rrhh_ausencia,
--    asi que el CASCADE del paso 1 ya la elimino, se deja el DROP
--    solo por si el CASCADE no llego a alcanzarla)
-- =====================================================================

DROP FUNCTION IF EXISTS public.detectar_solapamientos_horario(date, date);
DROP VIEW     IF EXISTS public.vista_ausencias_solapadas;


-- =====================================================================
-- 3. RECREAR respaldo_ejecucion, simple, solo para respaldo de fichas
-- =====================================================================

DROP TABLE IF EXISTS public.respaldo_ejecucion CASCADE;

CREATE TABLE public.respaldo_ejecucion (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_hora timestamptz NOT NULL DEFAULT now(),
    estado     text        NOT NULL,
    usuario_id bigint      REFERENCES public.usuario(id) ON DELETE NO ACTION,
    detalle    text,
    CONSTRAINT ck_respaldo_ejecucion_estado CHECK (estado IN ('exitoso','fallido'))
);


-- =====================================================================
-- Verificacion rapida (opcional): confirma que las tablas ya no existen
-- y que respaldo_ejecucion quedo con la estructura nueva.
-- =====================================================================
-- SELECT table_name FROM information_schema.tables
--  WHERE table_schema = 'public'
--    AND table_name IN ('horario','horario_jornada','asignacion_horario',
--        'rrhh_marcacion_asistencia','rrhh_ausencia','rrhh_feriado',
--        'rrhh_jornada_evaluacion','estadistica_indicador',
--        'estadistica_regla_correspondencia','estadistica_reporte',
--        'estadistica_reporte_version','estadistica_reporte_fuente',
--        'importacion_archivo','importacion_detalle',
--        'politica_conservacion','respaldo_restauracion');
-- (deberia devolver 0 filas)
