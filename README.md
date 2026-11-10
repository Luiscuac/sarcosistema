# SarcoSistema — Hospital Sarcobamba

Piloto académico con **datos ficticios**. Monolito modular: cada módulo mantiene sus reglas, casos de uso y adaptadores. El backend sigue arquitectura limpia: el router recibe HTTP, delega al caso de uso y convierte la respuesta. El dominio y la aplicación no dependen de FastAPI ni SQLAlchemy. No es una implementación clínica operativa ni una aprobación institucional.

## Stack

- **Backend:** Python 3.12 + FastAPI + PostgreSQL (pgvector) — ver `backend/`
- **Frontend:** React + Vite + Axios + React Query — ver `frontend/`
- **IA:** faster-whisper + Ollama local opcional para propuestas revisables

## Requisitos

- **Python 3.12**, versión utilizada por Docker y CI; en Windows se puede seleccionar con `py -3.12`.
- **Node.js y npm**. La verificación local de esta guía usa Node 24.14.0; el workflow de frontend está configurado con Node 20. No asumir que una ejecución local certifica otra versión de Node.
- **Docker Desktop iniciado**, para levantar PostgreSQL con Docker Compose.
- Ollama es opcional: el registro manual funciona sin IA.

Los comandos de Windows de esta guía son para **PowerShell** y parten de la raíz `sarcosistema/`, salvo que se indique otra carpeta. La activación de `.venv` es diferente en CMD o Bash; no mezcles los comandos entre terminales.

## Estructura

```text
backend/app/
  laboratorio/
    domain/           # entidades y reglas
    application/      # casos de uso y puertos
    infrastructure/   # adaptadores SQLAlchemy
    presentation/     # routers y esquemas HTTP
  accesos/
    application/      # caso de uso de inicio de sesión y puertos
    infrastructure/   # consultas SQL, JWT y hash de contraseñas
    presentation/     # endpoints y dependencias HTTP
  consultas/           # pacientes, historial, formulario SOAP y propuestas IA
  ia/                  # router común, whisper y transcriptor de prueba
  imagenes/            # módulo en construcción
  shared/             # utilidades verdaderamente transversales
  config/             # composición, configuración y sesión de BD

frontend/src/
  app/                 # aplicación, rutas y proveedores globales
  features/
    accesos/           # API, sesión, páginas y componentes de acceso
    inicio/            # páginas de inicio
    laboratorio/       # API, hooks, páginas y componentes de laboratorio
    consultas/         # ficha, historial, formulario y revisión de propuestas IA
    ia/                # grabación y transcripción reutilizables
  shared/              # cliente HTTP, UI y utilidades compartidas

transportador/          # agente Windows independiente; no lo inicia Compose
```

Los casos de uso dependen de protocolos (puertos); los adaptadores concretos se conectan en presentación/composición. Los repositorios llaman `flush()` y no confirman la transacción. `get_db` administra la transacción de cada operación HTTP para que los cambios coordinados se confirmen juntos.

## Primera preparación (Windows PowerShell)

### Backend (Windows PowerShell)

Desde la raíz del repositorio, inicia PostgreSQL y crea el entorno virtual **solo si todavía no existe**:

```powershell
docker compose up -d db
cd backend
if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    py -3.12 -m venv .venv
}
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
```

Activa el entorno e instala las dependencias del backend y las herramientas de desarrollo:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
```

**Ese es el comando de activación para PowerShell**, ejecutado desde `backend/`. En una terminal nueva, vuelve a esa carpeta y actívalo otra vez; no recrees `.venv`. Normalmente aparecerá `(.venv)` al inicio de la línea. Puedes comprobar el intérprete con:

```powershell
python -c "import sys; print(sys.executable)"
```

Debe apuntar a `sarcosistema\backend\.venv\Scripts\python.exe`. Para salir del entorno, ejecuta `deactivate`.

Si PowerShell bloquea `Activate.ps1`, **no necesitas permisos de administrador ni cambiar la política global**: usa directamente el intérprete del entorno. Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

Antes de migrar o iniciar el backend, configura `backend/.env` con `DATABASE_URL` y una `JWT_SECRET_KEY` larga y aleatoria. Para PostgreSQL del Compose, ejecutando Python en tu Windows:

```dotenv
DATABASE_URL=postgresql+asyncpg://hospital:hospital_dev_password@localhost:5432/hospital_sarcobamba
JWT_SECRET_KEY=reemplazar-por-una-clave-aleatoria-larga
DEBUG=true
WHISPER_MODEL_SIZE=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_MODEL_DIR=.models/whisper
WHISPER_CPU_THREADS=4
```

Las credenciales de Compose son **solo de desarrollo**. No sobrescribas un `.env` ya configurado ni subas secretos al repositorio. Si ejecutas el backend en Docker, Compose sobrescribe el destino de PostgreSQL con `db:5432`; dentro del contenedor, `localhost` no es el servicio de base de datos.

Para una base nueva, Docker Compose monta `database/schema.sql` como inicialización del servicio PostgreSQL. En ambos casos, después de comprobar que `backend/.env` apunta a la base correcta, ejecuta las migraciones incrementales desde `backend`:

```powershell
python -m alembic upgrade head
```

La revisión inicial comprueba que el esquema base ya existe; las siguientes revisiones agregan cambios sin recrearlo. En esta rama hay catorce revisiones y la cabecera es `20261109_0012` (unión de Laboratorio e IA). La reconciliación verificada está documentada en `docs/superpowers/plans/2026-11-09-reconciliar-migraciones.md`; no ejecutar `stamp` a ciegas si una instalación registra solo una rama aunque contiene objetos de ambas. Nunca vuelvas a ejecutar `schema.sql` sobre una base existente ni borres el volumen para resolver una conexión. Las instrucciones de laboratorio están en `docs/laboratorio/migraciones.md`.

Con el entorno activo y desde `backend`, verifica el esquema. Si necesitas una cuenta ficticia de Laboratorio, créala mediante el preparador:

```powershell
python -m scripts.verificar_esquema_accesos
python -m scripts.preparar_usuario_prueba laboratorio_prueba
```

El preparador de Laboratorio solicita contraseña y guarda su hash Argon2id; si la cuenta ya existe, puede renovar su contraseña. No lo ejecutes sobre una cuenta ajena sin autorización. Para crear el médico, su especialidad y el paciente **ficticios** de demostración:

```powershell
python -m scripts.preparar_medico_demo
```

Este segundo script muestra la ruta local de un archivo con la contraseña generada, no la imprime; se detiene si los registros de demostración ya existen. No hay que preparar usuarios en cada inicio.

### Frontend

En otra terminal, desde la raíz del repositorio, instala las dependencias una sola vez (o tras cambiar el lockfile):

```powershell
cd frontend
npm ci
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
```

El frontend no utiliza el entorno virtual de Python. `frontend/.env` permite configurar `VITE_API_URL=http://localhost:8000`.

## Uso diario (entorno ya preparado)

**Terminal 1**, desde la raíz:

```powershell
docker compose up -d db
cd backend
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

**Terminal 2**, también desde la raíz:

```powershell
cd frontend
npm run dev
```

Si no activaste `.venv`, sustituye los dos comandos `python -m ...` de la terminal del backend por estos, siempre desde `backend/` y con `.env` ya configurado:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- Aplicación: `http://localhost:5173` (usa **localhost**, origen permitido por CORS).
- Documentación del backend: `http://localhost:8000/docs`.
- Salud del proceso: `http://localhost:8000/health`; conexión a PostgreSQL: `http://localhost:8000/health/db`.
- Detener un servidor: `Ctrl+C` en su terminal; salir de `.venv`: `deactivate`.
- Tras cambiar de rama, reinicia uvicorn manualmente. Si 8000 o 5173 están ocupados, identifica el proceso antes de detenerlo; no levantes una segunda instancia ni cierres procesos ajenos.

## Activación en otras terminales

Todos estos comandos se ejecutan desde `backend/`:

| Terminal | Activar un entorno existente |
|---|---|
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| Linux/macOS, Bash o Zsh | `source .venv/bin/activate` |

En Linux/macOS, el entorno se crea con `python3.12 -m venv .venv`. **No reutilices la carpeta `.venv` de Windows en Linux ni al revés.** Sin activar, usa `./.venv/bin/python -m ...` en Linux/macOS o `.\.venv\Scripts\python.exe -m ...` en Windows.

## Transcripción y propuestas clínicas (opcionales)

El endpoint autenticado `POST /ia/transcribir` recibe un archivo de audio en el campo `archivo` (WAV, MP3, M4A, MP4, WebM, OGG, FLAC o MPEG; máximo 20 MB) y devuelve una transcripción en español. La primera solicitud descarga el modelo configurado si todavía no está en caché; el modelo se conserva en `WHISPER_MODEL_DIR` (en Compose, en el volumen `whisper_models`). El audio no se guarda en la base de datos. En Swagger (`/docs`), inicia sesión para obtener un bearer token y úsalo en **Authorize** antes de enviar el archivo. El texto es un borrador: el profesional debe revisarlo y confirmarlo, y no se publica automáticamente.

La configuración predeterminada usa el modelo multilingüe `small` en CPU con `int8` y cuatro hilos. Puedes cambiar el tamaño del modelo (`tiny`, `base`, `small`, `medium`, `large-v3`) y los parámetros de dispositivo/precisión mediante las variables `WHISPER_*`. El procesamiento se ejecuta localmente; la primera descarga del modelo sí requiere acceso a internet. Para instalar la dependencia Python, ejecuta `python -m pip install -r requirements.txt` desde `backend`.

Mantén el pin `av>=15,<17` de `requirements.txt`: PyAV 19 no es compatible con la llamada `metadata_errors` de faster-whisper 1.2.1.

### Consulta médica y dictado asistido

El rol `medico` accede a `/consultas`: búsqueda de pacientes, historial, registro SOAP y detalle en lectura. El panel de dictado reutiliza Whisper y propone campos mediante Ollama **local**; requiere revisión campo a campo y nunca guarda automáticamente. El formulario manual sigue disponible si el modelo falla. Configuración, privacidad, pruebas reales y limitaciones: [`docs/consultas/autocompletado-ia.md`](docs/consultas/autocompletado-ia.md). Preparación del módulo manual: [`docs/consultas/uso-y-migracion.md`](docs/consultas/uso-y-migracion.md).

El extractor viene deshabilitado en `.env.example`. Habilitarlo requiere configurar Ollama local y descargar el modelo aprobado; iniciar PostgreSQL o uvicorn no inicia Ollama. El agente `transportador/` es independiente y tampoco lo inicia este flujo.

### Visión de tórax experimental — Fase 2

El servicio opcional de TorchXRayVision analiza archivos locales en CPU y devuelve puntuaciones experimentales, no diagnósticos ni probabilidades clínicas calibradas. Los pesos se preparan antes de usarlo; no se descargan durante inferencia. Instalación, muestras NIH con atribución y prueba visual sin red: [`docs/imagenes/fase-2-vision-local.md`](docs/imagenes/fase-2-vision-local.md).

La integración actual agrega `/imagenes` para el médico solicitante: imagen autenticada, informe publicado de solo lectura, análisis controlado con RAG local y revisión explícita separada del diagnóstico. Requiere habilitación optativa, modelos/corpus preparados y migraciones; no necesita un LLM ni carga Torch al arrancar los módulos manuales. Preparación, demostración ficticia, pruebas reales y límites de la verificación offline: [`docs/imagenes/integracion-local.md`](docs/imagenes/integracion-local.md).

## Pruebas y comprobaciones

Backend, desde `backend/`, sin necesidad de activar `.venv`:

```powershell
.\.venv\Scripts\python.exe -c "import app.main"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas de integración requieren PostgreSQL **encendido**, `.env` correcto y migraciones aplicadas; trabajan con datos ficticios y rollback. `ConnectionRefusedError` o `WinError 1225` indican que hay que revisar la conexión, no desactivar pruebas. Las evaluaciones reales de Ollama/Whisper son optativas y están documentadas en la guía de autocompletado.

Frontend, desde `frontend/`:

```powershell
npm run lint
npm test
npm run build
```

No confundas “el entorno se activó” con “el backend y la base están funcionando”: son comprobaciones distintas.
