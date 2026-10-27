from dataclasses import dataclass


@dataclass(frozen=True)
class MedicoVigente:
    id: int
    especialidad_id: int


CLINICOS = frozenset({
    'diagnostico_principal', 'sintomas', 'enfermedad_actual', 'antecedentes',
    'examen_fisico', 'hallazgos', 'observaciones', 'evaluacion_clinica',
    'diagnosticos_secundarios', 'tratamiento', 'medicamentos', 'indicaciones',
    'estudios_solicitados', 'referencias', 'recomendaciones', 'plan_seguimiento',
    'peso_kg', 'talla_cm', 'temperatura_c', 'frecuencia_cardiaca',
    'frecuencia_respiratoria', 'presion_sistolica', 'presion_diastolica',
    'saturacion_oxigeno',
})
