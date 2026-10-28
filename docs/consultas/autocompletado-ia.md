# Dictado y propuestas SOAP con IA local

## Qué hace (y qué no hace)

El médico selecciona un paciente y abre **Nueva consulta**. El panel **Dictado asistido** reutiliza el `useAudioRecorder` existente y `POST /ia/transcribir` con faster-whisper en español. Al detener el audio, transcribe y solicita al extractor local que distribuya las frases entre los campos SOAP existentes.

La respuesta **no es una consulta** y no se guarda automáticamente. Cada propuesta muestra campo, valor editable y evidencia literal. El profesional puede aceptar un campo, rechazarlo o deshacer su aplicación. Un valor manual distinto exige confirmación de reemplazo. Deshacer no borra correcciones manuales posteriores. Mientras se está grabando/procesando o hay propuestas sin resolver, no se permite finalizar. Es posible cancelar o rechazar todas y continuar con el formulario manual si falla la IA.

La IA **no diagnostica ni prescribe**: solo propone información expresada. Conserva negaciones, sospechas, antecedentes y medicamentos literalmente; no agrega CIE-10. El modelo elige citas y campos; para narrativas el servidor copia la cita validada, no permite paráfrasis generadas. Se exige conservar la frase completa, no solo un fragmento que omita una negación o corrección. Un complemento determinista reconoce signos vitales explícitos para no depender de omisiones del LLM: verifica unidades, conversión de talla y correcciones verbales; mediciones contradictorias quedan ambiguas, nunca elige silenciosamente una. Si algo no se puede validar, se descarta con una advertencia; un campo ambiguo debe completarse manualmente. Si hay indicios de varios pacientes/identidad incierta, se bloquea todo el autocompletado.

Estas comprobaciones reducen riesgos, **no garantizan exactitud clínica**. Whisper actual no identifica hablantes ni devuelve confianza; el extractor no puede certificar que una conversación corresponde al paciente seleccionado ni detectar todos los errores o contradicciones. Hay que verificar persona, autor de cada frase, dosis y contenido antes de aceptar. El uso en este repositorio es con datos ficticios, no una aprobación institucional.

## Configuración local

1. Instalar Ollama en Windows desde su distribución oficial o `winget install --id Ollama.Ollama --exact --scope user`.
2. Ejecutar `ollama pull qwen2.5:3b` (~1,9 GB). No se descarga ningún modelo desde una petición clínica; si falta, el endpoint falla de forma recuperable. La primera ejecución carga el modelo y puede tardar más. Se evaluará latencia/calidad con pruebas ficticias; disponer de 15 GB de RAM no garantiza una velocidad específica mientras también corre Whisper.
3. En `backend/.env` (local, no versionado):

   ```dotenv
   CLINICAL_EXTRACTOR_ENABLED=true
   OLLAMA_URL=http://127.0.0.1:11434
   OLLAMA_MODEL=qwen2.5:3b
   CLINICAL_EXTRACTOR_TIMEOUT_SECONDS=180
   ```

   El valor predeterminado del extractor es **deshabilitado** para exigir configuración explícita. El adaptador rechaza direcciones externas, credenciales en URL, rutas arbitrarias y redirecciones. No utiliza proxies del entorno, SDK externo, herramientas, ejecución de comandos ni SQL generado por el modelo. Debe reiniciarse uvicorn tras cambiar `.env`.

4. Iniciar Ollama (aplicación o `ollama serve` si aún no hay servicio). No lanzar un segundo proceso si el puerto 11434 está ocupado por el Ollama existente.
5. Iniciar backend desde `backend`: `./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Iniciar frontend desde `frontend`: `npm run dev`. Abrir `http://localhost:5173` e iniciar sesión como médico.

En este entorno se fijó `av>=15,<17` (instalado PyAV 16.1.0): faster-whisper 1.2.1 usa `metadata_errors` y fallaba con PyAV 19. No se reemplazó Whisper ni su grabación. Para reproducir el entorno, instalar `pip install -r requirements.txt`. Comprobar también que el puerto de `DATABASE_URL` coincide con Docker; esta instalación publica la misma base existente en 5432. No reejecutar `schema.sql` ni borrar volúmenes para resolver un cambio de puerto.

Solo el adaptador local está implementado. El puerto `ExtractorClinico` permite añadir otra implementación en el futuro, pero cualquier infraestructura remota requeriría un cambio explícito autorizado de política de privacidad; no basta cambiar una URL para enviar datos fuera del equipo.

## Contrato backend

`POST /consultas/extraer-datos-clinicos`, con JWT de rol médico:

```json
{
  "paciente_id": 123,
  "transcripcion": "Motivo de consulta: dolor abdominal. Temperatura 37 grados."
}
```

Verifica paciente activo, 2–12000 caracteres, rol y esquema estricto del modelo. No transmite identidad, ID ni demografía del paciente a Ollama. Envía únicamente el dictado y las reglas de extracción; el dictado puede contener identificadores si el profesional los pronuncia, por eso el procesamiento queda en el equipo autorizado.

La respuesta contiene `propuesta_id`, `modelo`, `campos_extraidos` (`campo`, `valor`, `evidencia`, `ambiguo`), `advertencias`, `bloqueada` y `requiere_revision=true`. Se usan los nombres reales: `temperatura_c`, `antecedentes`, `hallazgos`, `estudios_solicitados`, `plan_seguimiento`; diagnósticos secundarios y medicamentos siguen siendo texto como en el formulario manual.

La extracción no escribe tablas clínicas ni guarda audio/transcripción. Hay timeout, límite de respuesta y una sola inferencia simultánea por proceso backend; no se cachean textos entre usuarios ni se reintenta automáticamente un análisis fallido. Un JSON envuelto solo en un bloque Markdown puede desempaquetarse, pero nunca se reparan inventando valores las respuestas inválidas.

Al guardar con el `POST /consultas` existente, el frontend puede enviar `revision_ia` (una revisión o lista de revisiones), con UUID de propuesta, nombre del modelo y nombres de campos aceptados. Se conservan solo esos **metadatos declarados por el médico** en `auditoria_accion.detalle`, dentro de la misma transacción de creación. No son una firma de la inferencia ni una certificación de exactitud. No se guardan transcripción, evidencia, valores propuestos rechazados ni tokens en la auditoría. Los campos clínicos confirmados se guardan igual que los manuales; sigue funcionando la protección idempotente previa. No hay migración de esquema.

## Audio y privacidad

- Confirmar autorización/consentimiento antes de grabar; una casilla de interfaz no sustituye los procedimientos y autorizaciones institucionales.
- Backend: el upload existente se cierra y sus bytes se descartan al completar la transcripción, sin conservación clínica en disco/BD. El archivo temporal de transporte de FastAPI también se cierra; no se implementa archivo histórico de audio.
- Navegador: el Blob y su URL se eliminan tras transcribir, al salir o al vencer `VITE_CLINICAL_AUDIO_TTL_SECONDS` (300 s por defecto; configurar en `frontend/.env`). Una grabación se detiene al alcanzar `VITE_CLINICAL_AUDIO_MAX_SECONDS` (180 s por defecto). No hay `localStorage`/`sessionStorage` de transcripciones. El texto original permanece en memoria para comparación hasta abandonar la consulta.
- Cancelar deja de aplicar resultados y cancela la petición del navegador. Una inferencia ya recibida por Ollama puede seguir ejecutándose hasta terminar o vencer su timeout; no se promete apagarla instantáneamente.
- No introducir transcripciones reales en pruebas, logs, URLs o mensajes de error. Los errores visibles del proveedor son genéricos. La auditoría contiene actor, acción, recurso, fecha y metadatos mínimos.

## Pruebas

Pruebas rápidas sin LLM:

```powershell
# backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
# frontend (otra terminal)
node --test src/features/consultas/utils/formulario.test.js src/features/consultas/utils/sugerencias.test.js src/features/laboratorio/utils/agruparSolicitudes.test.js
npm run lint
npm run build
```

Evaluación real optativa (necesita Ollama/modelo descargados; no usa dobles):

```powershell
# backend
$env:RUN_LOCAL_AI_TESTS='1'
.\.venv\Scripts\python.exe -m pytest tests/test_extraccion_modelo_local.py -v --tb=short
```

Para incluir Whisper y persistencia PostgreSQL, definir `LOCAL_AI_AUDIO_PATH` a un WAV **sintético/ficticio**. La prueba de integración crea un paciente de prueba dentro de una transacción, transcribe, extrae, realiza aceptación explícita de prueba, guarda con auditoría, relee y revierte todo. Requiere la cuenta `medico_demo` ya preparada. El test no sustituye pruebas clínicas humanas ni acredita exactitud general del modelo.

## Extensión

El proveedor está separado mediante `ExtractorClinico`; el formulario sigue usando un estado centralizado y aplica cambios campo a campo. Una integración futura puede usar datos estructurados más ricos o trazabilidad firmada, pero debe mantener evidencia, revisión humana, protección de manuales y guardado explícito. No implementar diagnósticos autónomos ni publicar al terminar una grabación.

## Evidencia de verificación local (28/10/2026)

- `pytest -q`: **83 passed, 2 skipped**; las dos pruebas lentas reales se omiten por defecto para no exigir descargas ni inferencias en CI.
- Evaluación optativa real con `RUN_LOCAL_AI_TESTS=1` y WAV sintético en español: **2 passed en 182,01 s**. Incluye ocho textos (completo, incompleto, desordenado, negación, ambigüedad, corrección, inyección, varios pacientes) y la cadena de audio real Whisper/Ollama/guardado/relectura/auditoría, con rollback. No se usó una grabación clínica real ni un micrófono físico en esa prueba.
- Node tests de formularios/sugerencias/Laboratorio: **11 passed**. `npm run lint`, `npm run build`, `pip check` e importación de `app.main`: correctos.
- `frontend/tests/consulta-ia.browser.js`: **5 comprobaciones PASS** en navegador real contra respuestas de API deliberadamente controladas, sin guardar consultas: reset de formulario al cambiar paciente; deshacer sin pisar decisiones manuales posteriores; cancelar e ignorar una respuesta tardía; caída de IA sin bloquear el formulario manual; permiso de micrófono pendiente que llega después de salir. Estas comprobaciones no se presentan como inferencia real; la inferencia real se comprueba por separado en backend.
- La revisión independiente detectó los fallos de estado por paciente, contexto recortado, micrófono pendiente y deshacer. Se reprodujeron antes de corregir y volvieron a pasar después. La caché de deduplicación de audio usa referencias débiles, no conserva Blobs históricos.
- Ollama `qwen2.5:3b` (~1,9 GB) quedó instalado en el equipo; `.env` local habilita el extractor. No se creó migración, no se modificó lógica de Laboratorio y no se dejaron consultas de prueba nuevas persistidas por las pruebas.

**Limitaciones:** superar estos ejemplos no mide sensibilidad/especificidad clínica ni garantiza que se reconozca toda conversación. Frases largas sin puntuación, abreviaturas, unidades no soportadas o transcripciones erróneas pueden descartarse o requerir edición manual. Un equipo ocupado puede agotar el timeout; el médico mantiene la vía manual. La atribución de hablantes y la resolución de identidades deben verificarse humanamente. La auditoría IA es declarativa, no una prueba criptográfica de procedencia.
