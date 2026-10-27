# SarcoSistema — Hospital Sarcobamba

Monolito modular: cada módulo mantiene sus reglas, casos de uso y adaptadores. En los módulos con flujo implementado, el backend sigue arquitectura limpia y usa MVC en presentación: el router recibe HTTP, delega al caso de uso y convierte la respuesta. El dominio y la aplicación no dependen de FastAPI ni SQLAlchemy.

## Stack

- **Backend:** Python + FastAPI + PostgreSQL (pgvector), en `backend/`
- **Frontend:** React + Vite + Axios + React Query, en `frontend/`
- **IA:** transcripción experimental con faster-whisper, ejecutada localmente dentro del backend

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
  ia/                 # endpoint y servicio local faster-whisper
  imagenes/            # módulo en construcción
  shared/             # utilidades verdaderamente transversales
  config/             # composición, configuración y sesión de BD

frontend/src/
  app/                 # aplicación, rutas y proveedores globales
  features/
    accesos/           # API, sesión, páginas y componentes de acceso
    inicio/            # páginas de inicio
    laboratorio/       # API, hooks, páginas y componentes de laboratorio
  shared/              # cliente HTTP, UI y utilidades compartidas
```

Los casos de uso dependen de protocolos (puertos); los adaptadores concretos se conectan en presentación/composición. Los repositorios llaman `flush()` y no confirman la transacción. `get_db` administra la transacción de cada operación HTTP para que los cambios coordinados se confirmen juntos.

## Desarrollo

### Backend (Windows PowerShell)

Desde la raíz del repositorio, inicia PostgreSQL y crea el entorno virtual de Python:

```powershell
docker compose up -d db
cd backend
py -3.12 -m venv .venv
```

Activa el entorno e instala las dependencias del backend y las herramientas de desarrollo:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
```

La activación solo es necesaria una vez por terminal. En una terminal nueva, vuelve a `backend` y ejecuta `.venv\Scripts\Activate.ps1`; no vuelvas a crear el entorno. Cuando esté activo, aparecerá `(.venv)` al inicio de la línea. Para salir, ejecuta `deactivate`.

Si PowerShell bloquea la activación del script, puedes ejecutar los comandos usando directamente el intérprete del entorno, sin activarlo:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Configura `backend/.env` con `DATABASE_URL` y `JWT_SECRET_KEY`. Para conectar con PostgreSQL iniciado mediante el Compose del proyecto, la URL local debe coincidir con sus credenciales, por ejemplo:

```dotenv
DATABASE_URL=postgresql+asyncpg://hospital:hospital_dev_password@localhost:5432/hospital_sarcobamba
JWT_SECRET_KEY=una-clave-local-larga
DEBUG=true
WHISPER_MODEL_SIZE=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_MODEL_DIR=.models/whisper
WHISPER_CPU_THREADS=4
```

Para una base nueva, Docker Compose monta `database/schema.sql` como inicialización del servicio PostgreSQL. En ambos casos, después de comprobar que `backend/.env` apunta a la base correcta, ejecuta las migraciones incrementales desde `backend`:

```powershell
alembic upgrade head
```

La revisión inicial comprueba que el esquema base ya existe; las siguientes revisiones agregan cambios sin recrearlo. Nunca vuelvas a ejecutar `schema.sql` sobre una base existente. Las instrucciones y el alcance de la primera migración de laboratorio están en `docs/laboratorio/migraciones.md`.

Con el entorno activo y desde `backend`, verifica el esquema, prepara una cuenta de prueba e inicia el servidor:

```powershell
python -m scripts.verificar_esquema_accesos
python -m scripts.preparar_usuario_prueba laboratorio_prueba
python -m uvicorn app.main:app --reload
```

La preparación de una cuenta solicita la contraseña interactivamente y guarda solo su hash Argon2id. El backend publica documentación en `http://localhost:8000/docs`.

### Transcripción experimental con faster-whisper

El endpoint autenticado `POST /ia/transcribir` recibe un archivo de audio en el campo `archivo` (WAV, MP3, M4A, MP4, WebM, OGG, FLAC o MPEG; máximo 20 MB) y devuelve una transcripción en español. La primera solicitud descarga el modelo configurado si todavía no está en caché; el modelo se conserva en `WHISPER_MODEL_DIR` (en Compose, en el volumen `whisper_models`). El audio no se guarda en la base de datos. En Swagger (`/docs`), inicia sesión para obtener un bearer token y úsalo en **Authorize** antes de enviar el archivo. El texto es un borrador: el profesional debe revisarlo y confirmarlo, y no se publica automáticamente.

La configuración predeterminada usa el modelo multilingüe `small` en CPU con `int8` y cuatro hilos. Puedes cambiar el tamaño del modelo (`tiny`, `base`, `small`, `medium`, `large-v3`) y los parámetros de dispositivo/precisión mediante las variables `WHISPER_*`. El procesamiento se ejecuta localmente; la primera descarga del modelo sí requiere acceso a internet. Para instalar la dependencia Python, ejecuta `python -m pip install -r requirements.txt` desde `backend`.

### Frontend

En otra terminal, desde la raíz del repositorio:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

La aplicación frontend se sirve en `http://localhost:5173`.
