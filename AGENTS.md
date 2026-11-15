# AGENTS.md — SarcoSistema

> Actualizado el 02/11/2026 contrastando rutas, scripts y configuración del árbol de trabajo. Activación PowerShell comprobada con Python 3.12.10. No asumir que PostgreSQL está iniciado ni reutilizar conteos de pruebas de otra sesión.

## Estructura

- **Backend** en `backend/app/`, imports `app.*`. Cada módulo sigue **arquitectura limpia** por carpeta: `domain/`, `application/`, `infrastructure/`, `presentation/`. Se prefieren *namespace packages*; existen paquetes de compatibilidad en Laboratorio y en `imagenes/application/ports/` (clínica y visión). No agregues `__init__.py` solo por costumbre.
- Módulos: `accesos` (login/JWT/roles), `laboratorio` (catálogo, solicitudes, muestras, resultados), `consultas` (pacientes, historial, SOAP, extracción asistida), `ia` (whisper + transcriptor), `imagenes` (visión CPU, RAG local y pantalla/API de revisión experimental optativa), `shared`, `config`.
- **Composición única de IA**: `app/ia/router.py` (prefijo `/ia`) incluye whisper y transcriptor. `main.py` incluye `app.ia.router`; **no** enlaces los routers internos de `ia/` directo (antes causaba `/ia/ia/transcribir`).
- Los repositorios hacen `flush()`; la transacción por petición la administra `get_db` (`SessionLocal.begin()`).
- **Frontend** en `frontend/src/`: `app/` (router + providers), `features/<modulo>/`, `shared/`. Pruebas con **`node:test`** (no vitest/jest): archivos `*.test.js` junto al código.
- `transportador/` es un agente Windows independiente con su propio `app/` y dependencias; no confundirlo con `backend/app/ia/transcriptor/`. Docker Compose no inicia el agente ni el frontend ni Ollama.

## Antes de editar

- Leer `README.md`, inspeccionar `git status --short --branch` y conservar cambios locales, incluso si la rama actual difiere de una sesión anterior. No hacer commits, push, reset ni limpieza destructiva sin autorización.
- Backend: usar Python 3.12 como Docker/CI; `pyproject.toml` declara un mínimo más amplio, no es evidencia de haber probado todas esas versiones. Frontend: comprobar Node/npm; la verificación local usa Node 24.14.0 y el workflow fija Node 20.
- Consultar `database/schema.sql` y migraciones antes de tocar persistencia. No inventar columnas, reejecutar el bootstrap sobre datos existentes ni borrar volúmenes. Cambios de esquema con Alembic incremental.
- Usar solo datos ficticios; no añadir farmacia, RRHH u otros módulos fuera del encargo. La IA no decide, diagnostica ni publica automáticamente; no enviar datos a proveedores externos sin autorización explícita.

## Entorno virtual y arranque (Windows PowerShell)

La preparación inicial, instalación y copia **sin sobrescribir** `.env` están en `README.md`. Crear `backend/.venv` solo una vez con `py -3.12 -m venv .venv`, desde `backend/`.

**Activación desde `backend/`:**

```powershell
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
```

El ejecutable debe pertenecer a `backend\.venv\Scripts\python.exe`. Reactivar en cada terminal nueva; salir con `deactivate`. CMD utiliza `.venv\Scripts\activate.bat`; Bash/Zsh en Linux/macOS utiliza `source .venv/bin/activate`. No usar `source` en PowerShell ni copiar `.venv` entre sistemas operativos. Si se bloquea `Activate.ps1`, usar el intérprete directo; no es necesario cambiar la política global de PowerShell.

**Uso diario desde la raíz, sin activación obligatoria:**

```powershell
docker compose up -d db
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head   # obligatorio
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

En **otra terminal**, también desde la raíz:

```powershell
cd frontend
npm run dev
```

- `backend/.env` y `frontend/.env` están en `.gitignore` (cambios locales). Credenciales del Compose: `hospital:hospital_dev_password@localhost:5432/hospital_sarcobamba`.
- Esas credenciales son de desarrollo. No imprimir JWT, contraseñas, hashes o transcripciones en logs; nunca versionar `.env` ni archivos locales de claves de demostración.
- Python ejecutado en Windows usa `localhost:5432`; el backend ejecutado dentro de Docker usa `db:5432` (override en Compose). No cambiar la URL local a `db` para ejecutar Python en el host.
- En esta rama hay veintidós revisiones Alembic, cabecera única `20261116_0018` (lectura médica en revisión IA), sobre `20261115_0017` (triaje IA de Rayos X) y `20261111_0016` (une `20261109_0014` y `20261110_0015`). RAG0008 fue distribuida con dos padres distintos: la correctiva y `scripts.reconciliar_historial_imagenes` cubren los historiales probados sin stamp. Antes de actualizar una instalación existente, revisar revisiones y ensayar en copia aislada; con dos cabezas IA/Laboratorio no usar upgrade head directo. Ver `docs/integracion/2026-11-10-resultado-integracion.md`. Para una base nueva, Compose inicializa el esquema; una base ya existente se conserva.
- Sin `alembic upgrade head` fallan pruebas que verifican `alembic_version` (p. ej. `tests/test_preparar_medico_demo.py`) y los flujos contra PostgreSQL.
- Tras **cambiar de rama**, reinicia uvicorn a mano: el watcher de `--reload` deja procesos viejos que se quedan con el puerto 8000 y código obsoleto.
- Ante un puerto ocupado, identificar proceso/comando antes de detenerlo; no cerrar procesos ajenos. CORS acepta `http://localhost:5173`, no intercambiarlo sin más por `http://127.0.0.1:5173`.

## IA y dependencia con trampa conocida

- `requirements.txt` fija `av>=15,<17`: **PyAV 19 retiró `metadata_errors`**, que usa `faster-whisper==1.2.1` al decodificar audio. Si instalas sin el pin, `/ia/transcribir` falla y `tests/test_whisper_audio_compatibilidad.py` lo detecta.
- Whisper y la grabación ya existen: reutilizar `POST /ia/transcribir` y el hook `useAudioRecorder`, no introducir otro motor de reconocimiento.
- La extracción se habilita explícitamente con `CLINICAL_EXTRACTOR_ENABLED=true`; adaptador Ollama solo en loopback, modelo configurable (predeterminado `qwen2.5:3b`). La URL `127.0.0.1` dentro de un contenedor no es Ollama del host: no solucionar esto abriendo destinos externos ni relajando privacidad sin autorización.
- Propuestas con evidencia, protección de campos manuales y guardado explícito. No retirar bloqueos de datos realmente ambiguos para hacer pasar pruebas; aislar el caso con texto ficticio y corregir su causa. No hay diarización ni confianza de Whisper en el contrato actual.
- Detalles de privacidad, retención en memoria, configuración y pruebas lentas: `docs/consultas/autocompletado-ia.md`.
- Visión de tórax Fase 2: dependencias **opcionales** `backend/requirements-radiologia-cpu.txt` y `requirements-radiologia.txt`; pesos se preparan solo con `scripts.preparar_modelos_radiologia --descargar`. Runtime carga safetensors local verificado, CPU y trabajador efímero con lock/timeout; no llamar al constructor XRV con pesos remotos desde inferencia. No importar Torch al arrancar los módulos manuales.
- Guía visual y prueba offline real (`Docker --network none`, sin tocar red del host): `docs/imagenes/fase-2-vision-local.md`. No introducir RAG/LLM/frontend en esta fase ni presentar scores como diagnósticos. `.models/`, `.datasets/` y resultados locales están fuera de Git; preservar procedencia/atribución de las muestras NIH.
- La integración posterior autorizada está en `docs/imagenes/integracion-local.md`: ruta `/imagenes`, médico solicitante, informe publicado solo lectura, modelos secuenciales y revisión append-only separada del diagnóstico. `RADIOLOGY_AI_ENABLED=false` por defecto; dependencias RAG opcionales. No introducir LLM nuevo ni auto-publicación. `.storage/` también está fuera de Git.
- Rayos X v2 (15/11/2026, `docs/imagenes/2026-11-15-evaluacion-externa-tb.md`): la entrada acepta PNG paleta/16 bits/RGBA, >16 MP (se reduce a 2048 px) y DICOM sin comprimir/RLE (`pydicom` opcional en `requirements-radiologia.txt`); `decodificar_radiografia`/`vista_previa_png` no importan Torch. El resultado añade `all_findings` (18), `indice_pulmonar` (artefacto `vision/indice_pulmonar_v1.json`, generado por `scripts.evaluacion_radiologia.tb_sonda`), `calidad` y `mapas_calor` (Grad-CAM); `findings` (3) se conserva para la fusión. Con `RADIOLOGY_AI_ENABLED=true`, subir una radiografía encola `imagen_triaje_ia` (solo visión) y la bandeja de Rayos X se ordena por prioridad; la cola atiende primero lo que pide el médico. Los umbrales de nivel son provisionales (`RADIOLOGY_TRIAGE_UMBRAL_ALTA/MEDIA`): no se transfieren entre hospitales. Las lecturas buscan en `IMAGENES_STORAGE_DIR` y `RADIOLOGY_STORAGE_DIR`. Shenzhen/Montgomery (NLM) en `.datasets/tb-nlm/` son solo para evaluar: no compartir fuera del grupo ni versionar.
- Rayos X v3 (15/11/2026): `fusionar_hallazgos` compara el informe en 18 categorías (por reglas, con negación, incertidumbre con alcance y posibles omisiones); no reemplazar por un LLM. RAG con 5 artículos abiertos (`scripts.preparar_rag_torax` agrega solo fuentes faltantes; el filtro XML `<!DOCTYPE` se mantiene por seguridad). DICOM JPEG/JPEG 2000 con `pylibjpeg` opcional. `imagen_revision_ia.anormal_confirmado` (opcional) alimenta `GET /imagenes/analisis/concordancia` y la calibración local (`application/calibracion.py`, mínimo 20 casos por clase; los umbrales sugeridos no se aplican solos). Segmentación pulmonar opcional (`scripts.preparar_segmentacion_pulmonar`, safetensors en `.models/radiologia-segmentacion`, `RADIOLOGY_LUNG_MASK_ENABLED`). Manual: `docs/imagenes/manual-uso-rayos-x.md`; instalación: `docs/imagenes/puesta-en-marcha-rayos-x.md`.
- Cierre documental 09/11/2026: las pruebas históricas y sus omisiones están en esa guía; Docker Linux no estaba disponible al retomar. No asumir el entorno levantado ni que sobreviven las bases tmpfs de prueba. No modificar credenciales locales para hacer pasar pruebas.

## Pruebas

- Backend, desde `backend/`: `.\.venv\Scripts\python.exe -c "import app.main"`, `.\.venv\Scripts\python.exe -m pip check` y `.\.venv\Scripts\python.exe -m pytest -q`. Necesita `.env` configurado o `DATABASE_URL`/`JWT_SECRET_KEY` exportadas como en CI.
- Las pruebas de PostgreSQL requieren BD encendida y migrada. Ante `ConnectionRefusedError`/`WinError 1225`, comprobar servicio, puerto y URL antes de modificar código o anular pruebas; distinguir ese fallo de un error de aplicación. Para aislar el primer fallo: `python -m pytest -q -x` con el entorno activo.
- `backend/conftest.py` provee `client` (httpx `ASGITransport`) y `usuarios` (parchea `SqlAlchemyUsuarioRepository` y anula `get_db`). Pruebas de integración en `backend/tests/` usan PostgreSQL real con rollback.
- Convención de pruebas nuevas: `app/<modulo>/tests/test_*.py`, dobles de repositorio/caso de uso con `app.dependency_overrides`, y verificación de que los errores de dominio no filtran detalles internos.
- Frontend: `npm test`, `npm run lint`, `npm run build` (los tres corre el CI).
- Las pruebas reales de IA son optativas (`RUN_LOCAL_AI_TESTS=1`); requieren Ollama/modelo disponibles. El flujo con audio requiere `LOCAL_AI_AUDIO_PATH` a un WAV ficticio. Reportar pruebas omitidas y fallos de entorno; no afirmar que el flujo real pasó si solo se usaron dobles.

## CI

- `backend-ci.yml`: `working-directory: backend`, servicio `pgvector/pgvector:pg16`, aplica `../database/schema.sql` y luego `alembic upgrade head`, y por último `pytest`.
- `frontend-ci.yml`: `npm ci` → `lint` → `test` → `build`.

## Corregido en esta rama (no volver a introducir)

- Carpeta `app/ia/Transporter` → **`app/ia/transcriptor`** (mayúscula inicial la hacía inimportable).
- `formatearFecha` interpreta las fechas de calendario (`YYYY-MM-DD`) como día local; antes se mostraba un día antes en zonas horarias negativas.
- `frontend/package.json` tenía pruebas (`*.test.js`) sin script `test` ni paso en CI.
- JWT requiere `exp` y `sub`; los cambios de sesión limpian la caché clínica de React Query. No conservar datos de una cuenta al entrar con otra.
- Laboratorio normaliza documentos, busca comodines literalmente y comprueba que un reenvío idempotente no cambie datos ni actor. La fecha generada por el servidor no debe impedir reintentos cuando el cliente no envió fecha.
- Consultas con JSON histórico incompatible no deben romper todo el historial ni sobrescribirse silenciosamente. Cancelar audio debe invalidar también eventos que lleguen después de `stop()`.

## Cuentas ficticias para probar

- No asumir usuarios, contraseñas o IDs sembrados en una instalación nueva.
- Desde `backend/` con entorno activo: `python -m scripts.verificar_esquema_accesos`; `python -m scripts.preparar_usuario_prueba <identificador>` prepara Laboratorio y pide contraseña interactivamente. Puede renovar la clave de una cuenta existente: no usarlo sobre cuentas ajenas sin autorización.
- `python -m scripts.preparar_medico_demo` crea `medico_demo`, su especialidad de prueba y el paciente `PAC-DEMO-CONSULTA-001` solo en PostgreSQL local migrado. Genera un archivo de clave fuera del repositorio, muestra su ruta y aborta si los registros ya existen. No crea una consulta clínica por sí solo.
