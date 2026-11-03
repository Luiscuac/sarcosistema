"""Versiona los formatos confirmados en las fichas del hospital.

Los resultados existentes conservan su versión anterior. Las nuevas capturas
usan la versión activa; no se reescriben informes ya publicados.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261102_0009"
down_revision = "20261102_0008"
branch_labels = None
depends_on = None


# código: (nombre, tipo, unidad, referencia). None conserva el dato anterior.
CAMBIOS = {
    "FORM_HEMOGRAMA_COMPLETO": {
        "gr": (None, None, None, "3,500,000 a 5,500,000/mm³"),
        "gb": ("Leucocitos (GB)", None, None, "4,000 a 10,000/mm³"),
        "hto": (None, None, None, "37 a 54 %"),
        "hb": (None, None, None, "11.0 a 16.0 g/dL"),
        "plaquetas": (None, None, None, "100,000 a 300,000/mm³"),
    },
    "FORM_EGO": {
        "color": (None, "cualitativo", None, "Amarillo; amarillo pálido; amarillo naranja"),
        "olor": (None, "cualitativo", None, "Sui géneris"),
        "aspecto": (None, "cualitativo", None, "Límpido"),
        "densidad": (None, "decimal", None, "1.010 a 1.025"),
        "ph": (None, None, None, "5.0 a 7.0"),
        "proteinas": (None, "texto", None, "Negativo"),
        "hemoglobina": ("Hemoglobina o sangre", "cualitativo", None, "Negativo"),
        "glucosa": (None, "decimal", "mg/dL", "0 mg/dL"),
        "cetonas": (None, "decimal", "mg/dL", "0 mg/dL"),
        "urobilina": (None, "texto", None, "Normal o 0 mg/dL"),
        "nitritos": (None, "cualitativo", None, "Negativo"),
        "leucocitos_quimico": (None, "cualitativo", None, "Negativo"),
        "bilirrubina": (None, "texto", None, "Negativo"),
        "celulas_epiteliales": (None, "texto", None, "Ausente a escaso"),
        "celulas_transicion": (None, "entero", "PCM", "0 a 1 PCM"),
        "celulas_redondas": ("Células renales", "texto", None, "Ausente"),
        "leucocitos_microscopico": (None, "entero", "PCM", "0 a 5 PCM"),
        "eritrocitos": (None, "entero", "PCM", "0 a 5 PCM"),
        "flora_bacteriana": (None, "cualitativo", None, "Ausente a escaso"),
        "filamentos_mucoides": ("Filamento mucoide", "cualitativo", None, "Ausente a escaso"),
        "trichomonas_vaginalis": (None, "cualitativo", None, "Ausente"),
        "cilindros_granulosos": (None, "entero", "PCM", "0 PCM"),
        "cilindros_hialinos": (None, "entero", "PCM", "0 a 1 PCM"),
        "cristales": (None, "texto", None, None),
    },
    "FORM_QUIMICA_SANGUINEA": {},
}

ADICIONES = {
    "FORM_HEMOGRAMA_COMPLETO": [
        ("vcm", "VCM", "decimal", "fL", "80 a 100 fL", 1),
        ("mch", "MCH", "decimal", "pg", "27 a 34 pg", 1),
        ("mchc", "MCHC", "decimal", "g/dL", "32 a 36 g/dL", 1),
        ("rdw_cv", "RDW-CV", "decimal", "%", "11.0 a 16.0 %", 1),
    ],
    "FORM_EGO": [
        ("volumen", "Volumen", "decimal", "mL", "10 a 50 mL", 1),
        ("levaduras", "Levaduras", "cualitativo", None, "Ausente", 2),
        ("piocitos", "Piocitos", "texto", None, "Ausente", 2),
        ("acumulos_leucocitarios", "Acúmulos leucocitarios", "texto", None, "Ausente", 2),
    ],
    "FORM_QUIMICA_SANGUINEA": [
        ("fosfatasa_alcalina", "Fosfatasa alcalina", "decimal", "U/L", "30 a 147 U/L", 1),
        ("amilasa", "Amilasa", "decimal", "U/L", "30 a 110 U/L", 1),
    ],
}

OPCIONES = {
    "color": ("Amarillo", "Amarillo pálido", "Amarillo naranja"),
    "olor": ("Sui géneris", "Fétido"),
    "aspecto": ("Límpido", "Ligeramente opalescente", "Opalescente"),
    "hemoglobina": ("Negativo", "+", "++", "+++"),
    "nitritos": ("Negativo", "Positivo"),
    "leucocitos_quimico": ("Negativo", "+", "++", "+++"),
    "flora_bacteriana": ("Ausente", "Escaso", "Regular", "Abundante"),
    "filamentos_mucoides": ("Ausente", "Escaso", "Regular", "Abundante"),
    "levaduras": ("Ausente", "Escaso", "Regular", "Abundante"),
    "trichomonas_vaginalis": ("Ausente", "Presente"),
}


def upgrade() -> None:
    bind = op.get_bind()
    for codigo_formato, cambios in CAMBIOS.items():
        plantilla = bind.execute(sa.text("""
            SELECT id FROM public.plantilla_examen WHERE codigo = :codigo
        """), {"codigo": codigo_formato}).scalar_one()
        anterior = bind.execute(sa.text("""
            SELECT id, numero_version FROM public.plantilla_examen_version
            WHERE plantilla_examen_id = :id AND estado = 'activa'
            ORDER BY numero_version DESC LIMIT 1
        """), {"id": plantilla}).mappings().one()
        nueva = bind.execute(sa.text("""
            INSERT INTO public.plantilla_examen_version
              (plantilla_examen_id, numero_version, estado, fecha_activacion,
               created_at, updated_at)
            VALUES (:plantilla, :numero, 'activa', now(), now(), now()) RETURNING id
        """), {"plantilla": plantilla, "numero": anterior["numero_version"] + 1}).scalar_one()
        secciones = bind.execute(sa.text("""
            SELECT id, nombre, orden FROM public.seccion_plantilla
            WHERE plantilla_version_id = :id ORDER BY orden
        """), {"id": anterior["id"]}).mappings().all()
        seccion_ids = {}
        for seccion in secciones:
            seccion_ids[seccion["id"]] = bind.execute(sa.text("""
                INSERT INTO public.seccion_plantilla (plantilla_version_id, nombre, orden)
                VALUES (:version, :nombre, :orden) RETURNING id
            """), {"version": nueva, "nombre": seccion["nombre"], "orden": seccion["orden"]}).scalar_one()
        parametros = bind.execute(sa.text("""
            SELECT * FROM public.parametro_plantilla WHERE plantilla_version_id = :id ORDER BY orden
        """), {"id": anterior["id"]}).mappings().all()
        for parametro in parametros:
            if codigo_formato == "FORM_QUIMICA_SANGUINEA" and parametro["codigo"] == "bun":
                continue  # El nombre estaba cubierto en la ficha; se excluye.
            cambio = cambios.get(parametro["codigo"], (None, None, None, None))
            nombre = cambio[0] or parametro["nombre"]
            tipo = cambio[1] or parametro["tipo_entrada"]
            unidad = cambio[2] or parametro["unidad"]
            referencia = cambio[3] or parametro["rango_referencia_texto"]
            nuevo_parametro = bind.execute(sa.text("""
                INSERT INTO public.parametro_plantilla
                  (plantilla_version_id, seccion_id, nombre, codigo, tipo_entrada,
                   unidad, rango_referencia_texto, valor_minimo, valor_maximo,
                   obligatorio, orden, precision_decimal)
                VALUES (:version, :seccion, :nombre, :codigo, :tipo, :unidad,
                        :referencia, NULL, NULL, :obligatorio, :orden, :precision)
                RETURNING id
            """), {
                "version": nueva, "seccion": seccion_ids.get(parametro["seccion_id"]),
                "nombre": nombre, "codigo": parametro["codigo"], "tipo": tipo,
                "unidad": unidad, "referencia": referencia,
                "obligatorio": parametro["obligatorio"], "orden": parametro["orden"],
                "precision": parametro["precision_decimal"],
            }).scalar_one()
            _opciones(bind, nuevo_parametro, parametro["codigo"])
        siguiente_orden = max(p["orden"] for p in parametros) + 1
        por_orden = {s["orden"]: seccion_ids[s["id"]] for s in secciones}
        for codigo, nombre, tipo, unidad, referencia, orden_seccion in ADICIONES[codigo_formato]:
            nuevo_parametro = bind.execute(sa.text("""
                INSERT INTO public.parametro_plantilla
                  (plantilla_version_id, seccion_id, nombre, codigo, tipo_entrada,
                   unidad, rango_referencia_texto, valor_minimo, valor_maximo,
                   obligatorio, orden, precision_decimal)
                VALUES (:version, :seccion, :nombre, :codigo, :tipo, :unidad,
                        :referencia, NULL, NULL, TRUE, :orden, NULL) RETURNING id
            """), {"version": nueva, "seccion": por_orden[orden_seccion],
                   "nombre": nombre, "codigo": codigo, "tipo": tipo,
                   "unidad": unidad, "referencia": referencia, "orden": siguiente_orden}).scalar_one()
            _opciones(bind, nuevo_parametro, codigo)
            siguiente_orden += 1
        bind.execute(sa.text("""
            UPDATE public.plantilla_examen_version SET estado = 'retirada', updated_at = now()
            WHERE id = :id
        """), {"id": anterior["id"]})


def _opciones(bind, parametro_id: int, codigo: str) -> None:
    for orden, etiqueta in enumerate(OPCIONES.get(codigo, ()), start=1):
        bind.execute(sa.text("""
            INSERT INTO public.opcion_parametro (parametro_id, codigo, etiqueta, orden, activo)
            VALUES (:parametro, :codigo, :etiqueta, :orden, TRUE)
        """), {"parametro": parametro_id, "codigo": str(orden),
               "etiqueta": etiqueta, "orden": orden})


def downgrade() -> None:
    raise RuntimeError(
        "La migración 20261102_0009 versiona formatos clínicos y no admite "
        "downgrade automático porque podría invalidar resultados existentes."
    )
