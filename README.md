# SarcoSistema — Hospital Sarcobamba

Monolito modular: cada módulo (`laboratorio`, `imagenes`, `accesos`, `ia`) sigue
capas tipo MVC (router → service → repository → models/schemas), con código
compartido en `shared/`.

## Stack

- **Backend:** Python 3.12 + FastAPI + PostgreSQL (pgvector) — ver `backend/`
- **Frontend:** React + Vite + Axios + React Query — ver `frontend/`
- **IA:** Whisper.cpp + Ollama, corriendo en servidor local (sin costo por uso)

## Cómo levantar el proyecto en desarrollo

```bash
# 1. Backend + base de datos
cd backend
cp .env.example .env          # completar DATABASE_URL y JWT_SECRET_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cd ..
docker compose up -d db
cd backend
alembic upgrade head           # cuando existan migraciones
uvicorn src.main:app --reload

# 2. Frontend (en otra terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```

Backend en `http://localhost:8000/docs` (documentación automática de FastAPI).
Frontend en `http://localhost:5173`.

## Estructura

```
backend/src/
  laboratorio/   imagenes/   accesos/   ia/     ← módulos del backlog
  shared/                                        ← código compartido
  config/                                        ← conexión BD, variables de entorno
frontend/src/
  components/  pages/  services/  hooks/  context/  routes/
```

## Convenciones de cada módulo backend

| Capa | Archivo | Equivale a (diagrama original) |
|---|---|---|
| Endpoints | `router.py` | `*.controller.ts` |
| Lógica de negocio | `service.py` | `*.service.ts` |
| Entidad / tabla | `models.py` | `*.entity.ts` |
| Forma de entrada/salida | `schemas.py` | `*.dto.ts` |
| Consultas a la BD | `repository.py` | `*.repository.ts` |
