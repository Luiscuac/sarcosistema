# AGENTS.md — SarcoSistema (rama `feature/transporter`)

> Verificado el 23/10/2026 levantando la rama completa: backend + frontend + BD.
> Ojo: versiones anteriores de este archivo describían otro layout del repo.

## Rama y layout (diferencias reales vs. lo que sugieren los nombres)

- Rama activa: `feature/transporter` (upstream `origin/feature/transporter`). El backend usa **`backend/app/`** e imports **`app.*`** (no `src.*`).
- Módulos backend en **arquitectura limpia** por carpeta: `domain/`, `application/`, `infrastructure/`, `presentation/` (p. ej. `app/laboratorio/presentation/router.py`, `app/accesos/application/use_cases/iniciar_sesion.py`). No busques `router.py`/`service.py`/`repository.py` sueltos: ya no existen.
- Frontend organizado por **features**: `src/features/<modulo>/{api,pages,components,hooks}` + `src/shared/` (httpClient, notifications, ui). Router: `src/app/router.jsx`.
- `transportador/` es un proyecto **independiente** (tiene su propio `requirements.txt` y `app/main.py`): **no** lo levanta `docker-compose.yml` ni el backend principal.
- `ia` usa **faster-whisper** local (`app/ia/whisper/...`); el modelo se descarga en la primera transcripción (~460 MB con `WHISPER_MODEL_SIZE=small`).

## Levantar el entorno (comandos exactos, Windows)

```powershell
docker compose up -d db                     # BD: hospital_sarcobamba, datos sembrados

# Backend — OJO: requiere el import previo de paciente (ver bugs).
cd backend
.\.venv\Scripts\python.exe -c "import app.shared.entities.paciente; import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000)"

# Frontend (otra terminal)
cd frontend
npm run dev                                  # http://localhost:5173
```

- `.env` está en `.gitignore` (`backend/.gitignore`, `frontend/.gitignore`): editarlos es cambio **local**, no del repo.
- `backend/.env` mínimo: `DATABASE_URL=postgresql+asyncpg://hospital:hospital_dev_password@localhost:5432/hospital_sarcobamba` + `JWT_SECRET_KEY`. `app/config/settings.py` los exige en el import.
- CORS solo acepta `http://localhost:5173`.
- Tras cambiar de rama, **reinicia uvicorn a mano** (no confíes en `--reload`: el watcher revive procesos viejos con código de la rama anterior y ocupa el puerto).

## Bugs conocidos de la rama (verificados, sin tocar)

1. **`POST /examenes` → 500 `NoReferencedTableError` ("could not find table 'paciente'")**: tras el refactor nadie importa `app/shared/entities/paciente.py` en tiempo de ejecución (solo `alembic/env.py`), así que SQLAlchemy no conoce el destino del FK `examen.paciente_id`. Fix de repo: agregar `from app.shared.entities import paciente` en `app/main.py`.
2. **`backend/tests/test_accesos.py` desactualizado**: manda `"contrasena"` (el schema pide `"password"` → 422 en vez de 401) y llama a `/accesos/me` (ruta real `/accesos/yo` → 404). Fallan 2 de 8 pruebas.
3. **`backend/create_test_user.py` roto**: importa `password_hasher`, ya inexistente (hoy es la clase `Argon2PasswordHasher`).
4. **Falta la tabla `examen`** en `database/schema.sql` y `alembic/versions/` está vacío → la BD local la tuve que crear a mano.
5. El repo quedó con `README.md` en **conflicto sin resolver (`UU`)** y un archivo basura `lkdjfa` sin trackear.

## Datos ficticios sembrados localmente (útiles para probar)

- Usuario: `lab_test` / `secreta123` (rol `laboratorio`, trabajador `T-999`).
- Paciente `PAC-DEMO-001` (id 1) + examen "Hemograma completo" (id 1).

## Pruebas y CI

- Backend: `pytest` desde `backend/`. `pyproject`: `pythonpath=["."]`, `testpaths=["app","tests"]`, `asyncio_mode="auto"`. La fixture `client` está en `backend/tests/conftest.py` (httpx `ASGITransport`); **las pruebas pegan contra la BD real** (no hay dobles): exporta `DATABASE_URL`/`JWT_SECRET_KEY` como hace el CI.
- CI: `.github/workflows/backend-ci.yml` (push/PR sobre `backend/**`, Python 3.12, `pytest`) y `frontend-ci.yml` (Node 20, `npm install && npm run build`).
