# AGENTS.md (SarcoSistema)

## Repo layout
- `backend/` FastAPI app in `app/` (modular: `accesos/`, `laboratorio/`, `imagenes/`, `ia/`, `shared/`, `config/`). Main: `app/main.py`.
- `frontend/` Vite + React (JSX). Entry: `src/main.jsx`, routes in `src/routes/AppRoutes.jsx`, API client in `src/services/api.js`.
- `database/schema.sql` mounted into Postgres on first init (docker-compose).
- `docker-compose.yml` brings up `db` (pgvector/pgvector:pg16). Backend/frontend run separately in dev.

## Dev commands (exact)
### Backend
```bash
cd backend
cp .env.example .env        # set DATABASE_URL, JWT_SECRET_KEY
python -m venv .venv && .\.venv\Scripts\activate  # Windows (or source .venv/bin/activate on Unix)
pip install -r requirements.txt -r requirements-dev.txt
# start DB
cd ..
docker compose up -d db
# migrate (Alembic)
cd backend
alembic upgrade head        # only if migrations exist
# run API
uvicorn app.main:app --reload  # note: app package is under backend/app (run from backend/ or set PYTHONPATH)
```
Notes from repo:
- Alembic env imports models: `app.laboratorio.models`, `app.shared.entities.paciente` (see `backend/alembic/env.py`). Add new models there if not auto-discovered.
- Settings require `DATABASE_URL`, `JWT_SECRET_KEY` (see `app/config/settings.py`). `.env` is loaded via `pydantic-settings`.
- DB is async SQLAlchemy (`app/config/database.py`). Health: `GET /health`, `GET /health/db`.

### Frontend
```bash
cd frontend
cp .env.example .env        # may not exist (see git history) - set VITE_API_URL
npm install
npm run dev                 # http://localhost:5173
npm run build
npm run lint
```
- API base URL comes from `import.meta.env.VITE_API_URL` (see `src/services/api.js`). Token attached from `localStorage.token` as `Authorization: Bearer ...`.
- Dev server port 5173 (vite.config.js). CORS allows `http://localhost:5173`.

### Tests
- Backend: `pytest` (from `backend/` or repo root as configured). `pytest.ini_options` has `pythonpath = ["."]`, `testpaths = ["app", "tests"]`, `asyncio_mode = "auto"`. Shared fixtures in `backend/tests/conftest.py` (httpx AsyncClient). Module test placeholder in `backend/app/laboratorio/tests/test_laboratorio.py`.
- CI: Backend runs on push/PR touching `backend/**` with Python 3.12, installs deps, runs `pytest` (sets `DATABASE_URL` and `JWT_SECRET_KEY` in env). Frontend builds on Node 20.

## Architecture notes (non-obvious)
- Module pattern per backend module: `router.py` (endpoints), `service.py` (business), `repository.py` (DB), `models.py` (SQLAlchemy), `schemas.py` (Pydantic). Mirrors MVC as described in README.
- Shared: `app/shared/` has `entities/` (e.g. `paciente.py`), `utils/`, `exceptions.py`, `validators.py`. Errors registered via `registrar_manejadores_de_error(app)`.
- DB init: docker-compose mounts `./database/schema.sql` to Postgres init dir; also Alembic migrations exist (`backend/alembic/`).
- IA module present (`app/ia/`) with router/transcripcion; images have storage logic (`app/imagenes/storage.py`). Treat as scaffolding unless needed.

## Gotchas
- Run backend from `backend/` directory (or ensure `PYTHONPATH` includes `backend/` because imports are `app.*`).
- `backend/.env` exists locally; `frontend/.env.example` was deleted in git history - if missing, create `.env` with `VITE_API_URL=http://localhost:8000`.
- CORS is locked to `http://localhost:5173`.
- Backend CI sets dummy env vars; local tests may need real DB or fixtures.
- README mentions Python 3.12 in Stack but text shows "### PYTHON 3.13 ###" as a heading - follow actual environment; CI uses 3.12.
