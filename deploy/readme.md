# Despliegue local en Windows

Esta guía levanta SarcoSistema en tu propia computadora con Docker Compose:
PostgreSQL, backend y frontend compilado.

No es un despliegue público ni reemplaza las revisiones de seguridad,
privacidad y aprobación institucional. Usa datos ficticios.

## Requisitos

- Docker Desktop iniciado.
- PowerShell.
- Puerto `5432` libre para el modo de desarrollo o el puerto `8080` libre
  para el despliegue local.

Ejecuta todos los comandos desde la raíz del repositorio
`sarcosistema`.

## Primera instalación

1. Copia el archivo de secretos sin sobrescribir uno existente:

```powershell
if (-not (Test-Path .\deploy\hospital.env)) {
    Copy-Item .\deploy\hospital.env.example .\deploy\hospital.env
}
```

2. Abre `deploy\hospital.env` y completa:

```dotenv
POSTGRES_DB=hospital_sarcobamba
POSTGRES_ADMIN_USER=sarcosistema_admin
POSTGRES_ADMIN_PASSWORD=contraseña-generada-por-ti
APP_DB_USER=sarcosistema_app
APP_DB_PASSWORD=otra-contraseña-generada-por-ti
JWT_SECRET_KEY=clave-aleatoria-larga-generada-por-ti
CORS_ALLOWED_ORIGINS=
```

Genera contraseñas y claves independientes con al menos 32 bytes aleatorios.
No reutilices las credenciales de desarrollo ni los valores vacíos del
archivo de ejemplo.

3. Decide desde qué dirección estará disponible la aplicación.

Para usarla únicamente en tu computadora, cambia en
`deploy\docker-compose.hospital.yml`:

```yaml
ports:
  - "127.0.0.1:8080:8080"
```

Para acceder desde otras computadoras de tu red local, reemplaza
`192.168.1.8` por la dirección IPv4 de tu computadora. Puedes verla con:

```powershell
(Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike "127.*" }).IPAddress
```

El servicio quedará publicado, por ejemplo, en
`http://192.168.1.8:8080`. Tu firewall debe permitir ese puerto únicamente
desde redes locales autorizadas.

4. Valida la configuración y construye los contenedores:

```powershell
docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml config -q

docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml build

docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml up -d
```

5. Espera a que estén saludables:

```powershell
docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml ps
```

Para una base completamente nueva, aplica las migraciones:

```powershell
docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml `
  exec backend python -m alembic upgrade head
```

No repitas este paso ni ejecutes `upgrade head` sobre una base existente
sin crear primero una copia de seguridad y seguir el procedimiento documentado
en `docs/integracion/2026-11-10-resultado-integracion.md` y
`docs/laboratorio/migraciones.md`.

## Uso diario

Inicia los servicios:

```powershell
docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml up -d
```

Abre `http://127.0.0.1:8080` si configuraste `127.0.0.1`, o usa la dirección
IPv4 configurada en el Compose.

Comprueba estado y logs:

```powershell
docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml ps

docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml logs --tail 100
```

Detén los servicios sin borrar los datos:

```powershell
docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml stop
```

Para volver a iniciarlos:

```powershell
docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml start
```

## Usuarios y datos

El despliegue no crea usuarios públicos ni datos reales. Las cuentas ficticias
se pueden preparar en un entorno de desarrollo mediante los scripts indicados
en el `README.md` principal.

Antes de usar datos reales se necesitan cuentas gestionadas, copias cifradas,
restauración probada, red restringida y aprobación de TI.

## Actualizar el proyecto

1. Conserva `deploy\hospital.env`.
2. Haz una copia de seguridad de los volúmenes y evita borrar volúmenes.
3. Actualiza el código o descarga la revisión aprobada.
4. Construye y reemplaza los contenedores:

```powershell
docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml build

docker compose --env-file deploy\hospital.env `
  -f deploy\docker-compose.hospital.yml up -d
```

Las migraciones no se ejecutan automáticamente. Revísalas y aplícalas
solo después de respaldar y ensayar sobre una copia de la base.