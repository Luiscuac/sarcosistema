# AGENTS.md — SarcoSistema

> Verificado el 28/10/2026 levantando la rama `main` (backend 143 pruebas, frontend 19).

## Estructura

- **Backend** en `backend/app/`, imports `app.*`. Cada módulo sigue **arquitectura limpia** por carpeta: `domain/`, `application/`, `infrastructure/`, `presentation/`. No hay `__init__.py`: se usan *namespace packages* (no los agregues solo por costumbre).
- Módulos: `accesos` (login/JWT/roles), `laboratorio` (catálogo, solicitudes, muestras, resultados), `consultas` (pacientes, historial, SOAP, extracción asistida), `ia` (whisper + transcriptor), `imagenes` (vacío), `shared`, `config`.
- **Composición única de IA**: `app/ia/router.py` (prefijo `/ia`) incluye whisper y transcriptor. `main.py` incluye `app.ia.router`; **no** enlaces los routers internos de `ia/` directo (antes causaba `/ia/ia/transcribir`).
- Los repositorios hacen `flush()`; la transacción por petición la administra `get_db` (`SessionLocal.begin()`).
- **Frontend** en `frontend/src/`: `app/` (router + providers), `features/<modulo>/`, `shared/`. Pruebas con **`node:test`** (no vitest/jest): archivos `*.test.js` junto al código.

## Levantar el entorno (Windows)

```powershell
docker compose up -d db
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head   # OBLIGATORIO: 7 migraciones
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
# otra terminal
cd frontend
npm run dev
```

- `backend/.env` y `frontend/.env` están en `.gitignore` (cambios locales). Credenciales del Compose: `hospital:hospital_dev_password@localhost:5432/hospital_sarcobamba`.
- Sin `alembic upgrade head` fallan pruebas que verifican `alembic_version` (p. ej. `tests/test_preparar_medico_demo.py`) y los flujos contra PostgreSQL.
- Tras **cambiar de rama**, reinicia uvicorn a mano: el watcher de `--reload` deja procesos viejos que se quedan con el puerto 8000 y código obsoleto.

## Dependencia con trampa conocida

- `requirements.txt` fija `av>=15,<17`: **PyAV 19 retiró `metadata_errors`**, que usa `faster-whisper==1.2.1` al decodificar audio. Si instalas sin el pin, `/ia/transcribir` falla y `tests/test_whisper_audio_compatibilidad.py` lo detecta.

## Pruebas

- Backend: `cd backend`, exporta `DATABASE_URL` y `JWT_SECRET_KEY` (los pone el CI) y ejecuta `pytest`. Suite completa ≈ 3.5 s; si hay un fallo aislado por entorno, confirma con `pytest -q -x`.
- `backend/conftest.py` provee `client` (httpx `ASGITransport`) y `usuarios` (parchea `SqlAlchemyUsuarioRepository` y anula `get_db`). Pruebas de integración en `backend/tests/` usan PostgreSQL real con rollback.
- Convención de pruebas nuevas: `app/<modulo>/tests/test_*.py`, dobles de repositorio/caso de uso con `app.dependency_overrides`, y verificación de que los errores de dominio no filtran detalles internos.
- Frontend: `npm test`, `npm run lint`, `npm run build` (los tres corre el CI).

## CI

- `backend-ci.yml`: `working-directory: backend`, servicio `pgvector/pgvector:pg16`, aplica `../database/schema.sql` y luego `alembic upgrade head`, y por último `pytest`.
- `frontend-ci.yml`: `npm ci` → `lint` → `test` → `build`.

## Corregido en esta rama (no volver a introducir)

- Carpeta `app/ia/Transporter` → **`app/ia/transcriptor`** (mayúscula inicial la hacía inimportable).
- `formatearFecha` interpreta las fechas de calendario (`YYYY-MM-DD`) como día local; antes se mostraba un día antes en zonas horarias negativas.
- `frontend/package.json` tenía pruebas (`*.test.js`) sin script `test` ni paso en CI.

## Datos ficticios locales para probar

- Usuario `lab_test` / `secreta123` (rol laboratorio). Paciente `PAC-DEMO-001` (id 1).
- `python -m scripts.preparar_medico_demo` y `python -m scripts.preparar_usuario_prueba <identificador>` crean cuentas ficticias (el segundo pide la contraseña de forma interactiva).
