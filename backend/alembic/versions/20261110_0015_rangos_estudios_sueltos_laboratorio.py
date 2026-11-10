"""Da unidad y rango de referencia a prestaciones de laboratorio solicitadas sueltas.

Como prestaciones sueltas usaban el formato libre v1 (resultado de texto, sin
referencia), aunque el mismo analito ya tenía rango en Química sanguínea o en el
Hemograma. Se activa una versión nueva con resultados numéricos, unidad y rango;
la versión anterior queda retirada y los resultados ya guardados conservan su
versión, como en 20261102_0009.

Rangos: fosfatasa alcalina y amilasa, confirmados por el laboratorio el
10/11/2026; el resto se copia de las versiones activas de FORM_QUIMICA_SANGUINEA
y FORM_HEMOGRAMA_COMPLETO (20261102_0009). VLDL no tiene rango confirmado.

Es idempotente: si la versión activa ya coincide con lo definido aquí, no crea
otra. Así puede convivir con bases donde el cambio se aplicó antes a mano.

NOTA DE INTEGRACIÓN: va después de 20261109_0013 (cabecera de main al integrar).
La rama de enfermería (20261107_0013 -> 20261109_0014) parte de 20261103_0009;
al integrarla, una de las dos cadenas debe continuar desde la otra.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261110_0015"
down_revision = "20261109_0013"
branch_labels = None
depends_on = None


def _unico(unidad: str, referencia: str) -> list[tuple]:
    return [("resultado", "Resultado", "decimal", unidad, referencia, True)]


# plantilla: [(codigo, nombre, tipo, unidad, referencia, obligatorio), ...]
FORMATOS = {
    "FORM_LIBRE_FOSFATASA_ALCALINA": _unico("U/L", "30 a 147 U/L"),
    "FORM_LIBRE_AMILASA": _unico("U/L", "30 a 110 U/L"),
    "FORM_LIBRE_GLICEMIA": _unico("mg/dL", "70–115 mg/dL"),
    "FORM_LIBRE_UREA": _unico("mg/dL", "10–50 mg/dL"),
    "FORM_LIBRE_CREATININA_SERICA": _unico("mg/dL", "0.6–1.3 mg/dL"),
    "FORM_LIBRE_ACIDO_URICO": _unico("mg/dL", "2.4–7.0 mg/dL"),
    "FORM_LIBRE_COLESTEROL_TOTAL": _unico("mg/dL", "Menor a 190 mg/dL"),
    "FORM_LIBRE_TRIGLICERIDOS": _unico("mg/dL", "Hasta 200 mg/dL"),
    "FORM_LIBRE_TRANSAMINASA_GOT": _unico("U/L", "Hasta 37 U/L"),
    "FORM_LIBRE_TRANSAMINASA_GPT": _unico("U/L", "Hasta 42 U/L"),
    "FORM_LIBRE_BILIRRUBINAS": [
        ("bilirrubina_total", "Bilirrubina total", "decimal", "mg/dL", "Hasta 1.0 mg/dL", True),
        ("bilirrubina_directa", "Bilirrubina directa (B.D.)", "decimal", "mg/dL", "Hasta 0.2 mg/dL", True),
        ("bilirrubina_indirecta", "Bilirrubina indirecta (B.I.)", "decimal", "mg/dL", "Hasta 0.8 mg/dL", True),
    ],
    "FORM_LIBRE_HEMOGLOBINA_HEMATOCRITO": [
        ("hb", "Hemoglobina (Hb)", "decimal", "g/dL", "11.0 a 16.0 g/dL", True),
        ("hto", "Hematocrito (Hto.)", "decimal", "%", "37 a 54 %", True),
    ],
    "FORM_LIBRE_PERFIL_LIPIDICO": [
        ("hdl_colesterol", "HDL-colesterol", "decimal", "mg/dL", "Mayor a 45 mg/dL", True),
        ("ldl_colesterol", "LDL-colesterol", "decimal", "mg/dL", "Menor a 190 mg/dL", True),
        ("vldl_colesterol", "VLDL-colesterol", "decimal", "mg/dL", None, False),
    ],
}


def _ya_aplicado(bind, version_id: int, parametros: list[tuple]) -> bool:
    actuales = bind.execute(sa.text("""
        SELECT codigo, tipo_entrada, unidad, rango_referencia_texto
          FROM public.parametro_plantilla WHERE plantilla_version_id = :version
    """), {"version": version_id}).all()
    esperados = {(c, t, u, r) for c, _n, t, u, r, _o in parametros}
    return {tuple(fila) for fila in actuales} == esperados


def aplicar(bind) -> None:
    for codigo, parametros in FORMATOS.items():
        plantilla = bind.execute(sa.text("""
            SELECT id FROM public.plantilla_examen WHERE codigo = :codigo
        """), {"codigo": codigo}).scalar_one_or_none()
        if plantilla is None:
            continue  # Base sin esa prestación: no hay nada que versionar.
        activa = bind.execute(sa.text("""
            SELECT id FROM public.plantilla_examen_version
             WHERE plantilla_examen_id = :id AND estado = 'activa'
             ORDER BY numero_version DESC LIMIT 1
        """), {"id": plantilla}).scalar_one_or_none()
        if activa is not None and _ya_aplicado(bind, activa, parametros):
            continue

        numero = bind.execute(sa.text("""
            SELECT COALESCE(MAX(numero_version), 0) + 1 FROM public.plantilla_examen_version
             WHERE plantilla_examen_id = :id
        """), {"id": plantilla}).scalar_one()
        if activa is not None:
            bind.execute(sa.text("""
                UPDATE public.plantilla_examen_version SET estado = 'retirada', updated_at = now()
                 WHERE id = :id
            """), {"id": activa})
        version = bind.execute(sa.text("""
            INSERT INTO public.plantilla_examen_version
                (plantilla_examen_id, numero_version, estado, fecha_activacion, created_at, updated_at)
            VALUES (:plantilla, :numero, 'activa', now(), now(), now()) RETURNING id
        """), {"plantilla": plantilla, "numero": numero}).scalar_one()
        seccion = bind.execute(sa.text("""
            INSERT INTO public.seccion_plantilla (plantilla_version_id, nombre, orden)
            VALUES (:version, 'Resultado', 1) RETURNING id
        """), {"version": version}).scalar_one()
        for orden, (cod, nombre, tipo, unidad, referencia, obligatorio) in enumerate(parametros, start=1):
            bind.execute(sa.text("""
                INSERT INTO public.parametro_plantilla
                    (plantilla_version_id, seccion_id, nombre, codigo, tipo_entrada,
                     unidad, rango_referencia_texto, valor_minimo, valor_maximo,
                     obligatorio, orden, precision_decimal)
                VALUES (:version, :seccion, :nombre, :codigo, :tipo,
                        :unidad, :referencia, NULL, NULL, :obligatorio, :orden, NULL)
            """), {"version": version, "seccion": seccion, "nombre": nombre, "codigo": cod,
                   "tipo": tipo, "unidad": unidad, "referencia": referencia,
                   "obligatorio": obligatorio, "orden": orden})


def upgrade() -> None:
    aplicar(op.get_bind())


def downgrade() -> None:
    raise RuntimeError(
        "La migración 20261110_0015 versiona formatos clínicos y no admite "
        "downgrade automático porque podría invalidar resultados existentes."
    )
