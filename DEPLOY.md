# Despliegue de SarcoSistema

Configuración inicial para Vercel (frontend), Render (API FastAPI) y Neon (PostgreSQL). El proyecto está preparado para un piloto con datos ficticios; estos pasos no constituyen aprobación para uso clínico ni validación de requisitos regulatorios.

## 1. Crear la base en Neon

1. Crea un proyecto PostgreSQL en Neon y elige una región cercana a la región que usarás en Render.
2. Copia la URL de conexión **pooled**. El backend usa `asyncpg`, así que cambia el prefijo `postgresql://` por `postgresql+asyncpg://` si Neon no lo entrega así. Conserva los parámetros TLS de Neon (`sslmode=require`). No publiques esta URL.
3. Las migraciones de este repositorio esperan que exista el esquema base. En una base Neon vacía, ejecuta una sola vez `database/schema.sql` con una herramienta PostgreSQL conectada a esa base. Después aplica Alembic como se indica abajo. Nunca ejecutes el bootstrap sobre una base existente.

## 2. Crear el servicio Render

1. En Render selecciona **New → Blueprint** y conecta este repositorio. Render leerá `render.yaml` y construirá la imagen desde `backend/Dockerfile`.
2. En las variables del servicio configura:
   - `DATABASE_URL`: URL de Neon adaptada a `postgresql+asyncpg://`.
   - `CORS_ORIGINS`: origen Vercel exacto, por ejemplo `https://sarcosistema.vercel.app` (sin barra final). Puedes añadir varios separados por comas.
3. Render generará `JWT_SECRET_KEY`. Guárdala en el panel de Render y no la cambies tras crear sesiones/usuarios.
4. El Blueprint solicita un disco persistente de 10 GB en `/var/data` para archivos de imágenes. Ajusta el tamaño en Render a las necesidades reales. Si el plan no permite discos persistentes, no habilites carga/almacenamiento de archivos clínicos en ese servicio.
5. Una vez creado el servicio, abre **Shell** en Render y ejecuta:

   ```sh
   cd /app
   python -m alembic upgrade head
   ```

   En una base vacía aplica primero `database/schema.sql` localmente contra Neon; en una base existente revisa el historial y ensaya la actualización en una copia antes de migrar. Este proyecto tiene historial de revisiones ramificado; no automatices `upgrade head` durante cada arranque.

La API estará en `https://<servicio>.onrender.com`; comprueba `/health` y `/health/db`.

## 3. Crear el frontend Vercel

1. Importa el repositorio en Vercel. El archivo `vercel.json` configura el build y las rutas SPA.
2. Configura **Root Directory** como `frontend`.
3. Añade la variable de entorno de producción `VITE_API_URL` con la URL Render del backend, sin barra al final, por ejemplo `https://sarcosistema-api.onrender.com`.
4. Despliega y copia el dominio final de Vercel.
5. Si cambia el dominio Vercel, actualiza `CORS_ORIGINS` en Render y vuelve a desplegar el backend.

## Variables de entorno

| Servicio | Variable | Valor |
| --- | --- | --- |
| Render | `DATABASE_URL` | URL Neon con prefijo `postgresql+asyncpg://` |
| Render | `JWT_SECRET_KEY` | Generada por Render en el Blueprint |
| Render | `CORS_ORIGINS` | Uno o más orígenes Vercel separados por coma |
| Render | `DEBUG` | `false` |
| Vercel | `VITE_API_URL` | URL pública del backend Render |

No configures `DATABASE_URL` ni `JWT_SECRET_KEY` en Vercel: el navegador no debe recibir secretos de backend.
