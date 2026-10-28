# Autocompletado clínico Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reutilizar Whisper y distribuir dictado en propuestas SOAP, revisadas antes de persistir.
**Architecture:** Puerto desacoplado, Ollama HTTP local, validación defensiva, endpoint médico, panel con aceptación explícita sobre estado centralizado.
**Tech Stack:** FastAPI/Pydantic/httpx, React/React Query, Whisper existente, Ollama `qwen2.5:3b`.
**Spec:** `docs/superpowers/specs/2026-10-27-autocompletado-clinico-design.md`

## Global Constraints
- No enviar datos clínicos fuera de loopback; sin nuevos SDK ni librería de grabación, sin migraciones.
- No reemplazar texto manual sin consentimiento, no guardar automáticamente, no diagnosticar.
- Modelos descargados solo con autorización recibida; secretos y `.env` fuera de git.
- No commits/push ni cambios en Laboratorio.

## Review Focus
- Respuesta asíncrona tras cambiar paciente/desmontar no debe aplicar propuestas antiguas (Task 3).
- Evidencia que recorta negaciones o modifica dosis debe excluirse (Task 1).
- Servicio caído nunca impide consulta manual (Tasks 2–3).
- Petición/cancelación/reintento no debe duplicar ni conservar audio indefinidamente (Task 3).
- Auditoría no debe contener transcripción, token ni evidencia literal (Task 2).

### Task 1: Contrato, validación y proveedor local
**Files:** `backend/app/consultas/domain/extraccion.py`, `backend/app/consultas/application/ports/extractor_clinico.py`, `backend/app/consultas/infrastructure/ia/{ollama,prompt}.py`, `backend/app/config/settings.py`, `backend/.env.example`, `backend/tests/test_extraccion_clinica.py`.
**Interfaces:** `ExtractorClinico.extraer(transcripcion: str) -> PropuestaClinica`; esquemas/validación con nombres reales y evidencia literal, bloqueo por identidad múltiple.
- [x] Escribir pruebas de nueve ejemplos ficticios, evidencia/negación/medicación, JSON inválido y URL remota.
- [x] Ejecutar pytest y observar fallo por funcionalidad ausente.
- [x] Implementar puerto y proveedor httpx con schema estricto, timeout y semáforo; validación sin completar ausentes.
- [x] Ejecutar pruebas y comprobar PASS.

### Task 2: Endpoint y trazabilidad de guardado
**Files:** `backend/app/consultas/presentation/{router,schemas}.py`, `backend/app/consultas/application/use_cases/extraer_datos_clinicos.py`, `backend/app/consultas/infrastructure/persistence/repository.py`, `backend/tests/test_extraccion_api.py`.
**Interfaces:** `POST /consultas/extraer-datos-clinicos {paciente_id,transcripcion}` devuelve `{campos_extraidos,advertencias,bloqueada,requiere_revision,propuesta_id,modelo}`; `revision_ia` opcional al crear, solo metadatos.
- [x] Pruebas RED de RBAC, paciente, texto, errores 503/502, no escritura ni información clínica en error.
- [x] Implementar endpoint/caso de uso y validación de `revision_ia`, auditoría atómica sin transcripción.
- [x] GREEN de pruebas backend, manual e integración PostgreSQL.

### Task 3: Reutilización de grabación y revisión segura en React
**Files:** `frontend/src/features/consultas/{components/AsistenteClinico.jsx,utils/sugerencias.js,utils/sugerencias.test.js}`, `ConsultaFormulario.jsx`, `api/consultasApi.js`, `pages/consultas.css`, `frontend/.env.example`.
**Interfaces:** asistente recibe `pacienteId`, valores actuales y callback de cambios puntuales; no altera función de guardado; todas las sugerencias pendientes bloquean finalizar hasta aceptación o rechazo.
- [x] RED Node tests de protección de manuales, conflicto, aceptación, deshacer, cambio posterior y bloqueo.
- [x] Implementar panel con hook audio existente, API Whisper existente, análisis automático y cancelación/TTL; CSS del módulo, sin nuevo dashboard.
- [x] GREEN Node tests, lint y build.

### Task 4: Evaluación real, revisión y documentación
**Files:** `docs/consultas/autocompletado-ia.md`, pruebas optativas de modelo real.
- [x] Instalar Ollama/descargar modelo autorizado, configurar localmente y probar endpoint real con datos ficticios.
- [x] Probar Whisper con audio sintético si el sistema permite generarlo sin dependencias nuevas; guardar solo después de revisión explícita en prueba PostgreSQL revertida.
- [x] Ejecutar pytest completo, Node tests, pip check, import, lint y build.
- [x] Revisión independiente, corregir problemas relevantes con prueba RED→GREEN; documentar limitaciones y resultados reales.

## Registro de ejecución

Inicio: rama actual autorizada `features/historia_clinica`, árbol limpio. No se crea worktree (preferencia explícita previa). Las interfaces comparten nombres de `ConsultaNueva`; se excluye `revision_ia` de contenido clínico/idempotencia. Regla: el proveedor solo hace propuestas, nunca escribe en BD. La autorización inicial del usuario incluye ejecutar después del plan breve; no se añaden rondas de aprobación redundantes.

28/10: Tasks 1–4 completas. Verificación final: 83 pruebas rápidas backend, 2 evaluaciones reales (incluyen 8 dictados y WAV sintético/Whisper/Ollama/BD), 11 pruebas Node, 5 escenarios de navegador con API controlada; lint/build/pip check/import correctos. No commits solicitados ni realizados.

Ruling: El modelo pequeño no reproducía consistentemente valor/evidencia y omitía medidas; se simplificó a selección de citas y se complementó con verificación determinista de medidas explícitas. No se generan hechos ni dosis; coste: frases/unidades fuera del subconjunto admitido requieren captura manual.

Ruling: Evidencia recortada se rechaza si no conserva la frase completa; seguridad sobre recall. Coste: algunas propuestas válidas pero demasiado cortas se descartan con aviso.

Ruling: Se fijó PyAV a >=15,<17 tras reproducir el error metadata_errors con PyAV 19. Se reutilizó Whisper sin reimplementarlo; coste: revisar compatibilidad cuando se actualice faster-whisper.

Ruling: La auditoría conserva una lista de metadatos de revisiones declaradas por médico (sin texto, evidencia ni tokens), no certifica el origen del modelo. Coste: no es trazabilidad firmada de inferencias; limitación documentada.

Revisión: correcciones verificadas RED→GREEN de contaminación entre pacientes, recorte de negaciones/correcciones, inicio tardío de micrófono y deshacer tras decisión manual posterior. Sin pendientes críticos/importantes conocidos en la revisión; evaluación clínica institucional y micrófono físico no se simulan como aprobados.
