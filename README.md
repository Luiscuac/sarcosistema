# SarcoSistema — Hospital Sarcobamba

Monolito modular: cada módulo mantiene sus reglas, casos de uso y adaptadores. En los módulos con flujo implementado, el backend sigue arquitectura limpia y usa MVC en presentación: el router recibe HTTP, delega al caso de uso y convierte la respuesta. El dominio y la aplicación no dependen de FastAPI ni SQLAlchemy.

## Stack

- **Backend:** Python + FastAPI + PostgreSQL (pgvector), en `backend/`
- **Frontend:** React + Vite + Axios + React Query, en `frontend/`
- **IA:** componentes experimentales y sin flujo funcional integrado

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
  imagenes/ ia/       # módulos esqueleto hasta que tengan casos de uso
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

Configura `backend/.env` con `DATABASE_URL` y `JWT_SECRET_KEY`. Para una base nueva, Docker Compose monta `database/schema.sql` como inicialización del servicio PostgreSQL. Para una base existente, no vuelvas a inicializar ni sobrescribas el esquema; aplica el procedimiento acordado con el equipo.

Desde `backend`, con dependencias instaladas:

```powershell
.venv\Scripts\python.exe -m scripts.verificar_esquema_accesos
.venv\Scripts\python.exe -m scripts.preparar_usuario_prueba laboratorio_prueba
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La preparación de una cuenta solicita la contraseña interactivamente y guarda solo su hash Argon2id. El backend publica documentación en `http://localhost:8000/docs`.

En otra terminal:

```powershell
cd frontend
npm run dev
```

La aplicación frontend se sirve en `http://localhost:5173`.
