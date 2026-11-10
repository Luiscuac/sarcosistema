# AGENTS.md — SarcoSistema

> Actualizado el 02/11/2026 contrastando rutas, scripts y configuración del árbol de trabajo. Activación PowerShell comprobada con Python 3.12.10. No asumir que PostgreSQL está iniciado ni reutilizar conteos de pruebas de otra sesión.

## Estructura

- **Backend** en `backend/app/`, imports `app.*`. Cada módulo sigue **arquitectura limpia** por carpeta: `domain/`, `application/`, `infrastructure/`, `presentation/`. No hay `__init__.py`: se usan *namespace packages* (no los agregues solo por costumbre).
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
- En esta rama hay nueve revisiones Alembic, cabecera `20261103_0009` (0008 corpus pgvector, 0009 análisis/revisión experimental de imágenes). Para una base nueva, Compose inicializa el esquema; después siempre aplicar migraciones. Una base ya existente se conserva.
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
