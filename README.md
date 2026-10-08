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
# 1. Backend + base de datos (solo en una instalación nueva)
cd backend
cp .env.example .env          # completar DATABASE_URL y JWT_SECRET_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cd ..
docker compose up -d db
cd backend
alembic upgrade head           # solo si existen migraciones pendientes
uvicorn app.main:app --reload

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

## Primer flujo: acceso a laboratorio con base existente

Si PostgreSQL ya tiene el esquema, no ejecutes `database/schema.sql` ni vuelvas a
crear la base. Configura `DATABASE_URL` y una clave aleatoria larga en
`JWT_SECRET_KEY` en el entorno local del backend, sin subirlas a Git. Configura
`VITE_API_URL=http://localhost:8000` para el frontend.

Desde `backend`, en Windows y con el entorno virtual instalado:

```powershell
.venv\Scripts\python.exe -m scripts.verificar_esquema_accesos
.venv\Scripts\python.exe -m scripts.preparar_usuario_prueba laboratorio_prueba
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

El comando `preparar_usuario_prueba` solicita la contraseña de forma interactiva
y guarda solo el hash Argon2id. Si la cuenta aún no existe, requiere un trabajador
ficticio activo ya cargado y la opción `--trabajador-id ID`; crea la cuenta con
el rol `laboratorio`. No cambia una cuenta de otro rol. Con una cuenta existente,
omite esa opción para renovar su contraseña de prueba.

En otra terminal, desde `frontend`:

```powershell
npm run build
npm run dev
```

Abre `http://localhost:5173/login`. El acceso es común para todos los roles:
una cuenta de laboratorio entra a `/laboratorio` y los demás roles llegan a
`/inicio`, donde se indica que su módulo aún no forma parte del piloto.
Una contraseña errónea muestra un error. Abre `/laboratorio` sin sesión o tras
cerrar sesión para comprobar la redirección.
