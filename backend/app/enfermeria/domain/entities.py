"""Reglas de estado para los registros de admisión de enfermería."""

ESTADO_BORRADOR = 'borrador'
ESTADO_PUBLICADO = 'publicado'

MEDICIONES = (
    'peso_kg', 'talla_cm', 'temperatura_c', 'frecuencia_cardiaca',
    'frecuencia_respiratoria', 'presion_sistolica', 'presion_diastolica',
    'saturacion_oxigeno', 'dolor_escala',
)

NARRATIVAS = ('motivo_consulta', 'sintomas', 'observaciones_enfermeria')
CAMPOS_REGISTRO = NARRATIVAS + MEDICIONES
