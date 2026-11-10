"""Contexto léxico y de formato para la transcripción médica en español."""

# faster-whisper usa initial_prompt como contexto del decodificador; no es una
# instrucción estricta. Los ejemplos orientan la puntuación sin completar datos.
PROMPT_TRANSCRIPCION = (
    "Consulta médica en español. Transcribe literalmente lo que se escucha; "
    "conserva negaciones y no agregues información. Usa puntuación clara y, "
    "cuando se dicten, escribe estos rótulos con dos puntos: "
    "Motivo de consulta: … Síntomas: … Enfermedad actual: … Antecedentes: … "
    "Al examen físico: … Temperatura: … Pulso: … Presión sistólica: … "
    "Presión diastólica: … Saturación de oxígeno: … Plan: … Seguimiento: …"
)
