# Despliegue de referencia en intranet hospitalaria

Esta guía prepara contenedores para una instalación gestionada por TI del hospital. **No certifica el sistema para uso clínico ni sustituye la revisión de seguridad, privacidad, continuidad y aprobación institucional.** El README describe este proyecto como piloto académico; hasta completar esas revisiones, usa exclusivamente datos ficticios.

## Arquitectura

- El contenedor `frontend` sirve la compilación de React y envía `/api/*` al backend.
- Solo publica `127.0.0.1:8080` en el servidor. El proxy inverso aprobado por el hospital debe terminar HTTPS con un certificado de confianza para el nombre DNS interno y reenviar a ese puerto.
- El backend y PostgreSQL no publican puertos del host. La base está en una red Docker separada y la aplicación usa un rol PostgreSQL distinto del administrador.
- La configuración de producción permite iniciar sesión solo a `medico`, `laboratorio` y `enfermeria`. Las rutas de cada módulo conservan además sus controles de rol. No hay registro público.

## Requisitos previos del hospital

TI debe proporcionar un servidor Linux administrado, DNS interno, TLS de confianza para los dispositivos clínicos, reglas de firewall que permitan el acceso solo desde las redes autorizadas y un procedimiento de gestión de usuarios. Restringe el acceso al puerto HTTPS del proxy a la intranet clínica; no publiques `5432`, `8000` ni el puerto local `8080`. Limita el acceso al grupo Docker: quien controla Docker puede acceder a los datos del servidor.

Configura el proxy inverso del host para redirigir HTTP a HTTPS y enviar el tráfico HTTPS al backend local `http://127.0.0.1:8080`, conservando las rutas `/` y `/api/`. El proxy debe sobrescribir `X-Forwarded-Proto` con `https`, admitir cuerpos de hasta 101 MB y aplicar los límites de acceso aprobados por TI. No uses un certificado autofirmado sin distribuir y confiar la CA institucional en todos los dispositivos autorizados.

## Secretos y arranque

Desde la raíz del repositorio, crea el archivo local ignorado por Git:

```sh
cp deploy/hospital.env.example deploy/hospital.env
```

Completa los secretos con valores únicos generados para esta instalación. Usa contraseñas aleatorias hexadecimales para los dos roles PostgreSQL y un `JWT_SECRET_KEY` de al menos 32 bytes aleatorios; no reutilices secretos de desarrollo. Protege `deploy/hospital.env` con permisos solo para administradores del servidor. `POSTGRES_ADMIN_USER` es el rol de migración/administración; la aplicación recibe únicamente `APP_DB_USER` y `APP_DB_PASSWORD`.

Valida la configuración y construye los servicios:

```sh
docker compose --env-file deploy/hospital.env -f deploy/docker-compose.hospital.yml config -q
docker compose --env-file deploy/hospital.env -f deploy/docker-compose.hospital.yml build
docker compose --env-file deploy/hospital.env -f deploy/docker-compose.hospital.yml up -d
```

La primera inicialización de una base vacía aplica `database/schema.sql` y crea el rol de aplicación con permisos DML. Los scripts de inicialización de PostgreSQL **solo se ejecutan cuando el volumen de datos está vacío**. No borres volúmenes ni repitas el bootstrap para actualizar una instalación existente.

Las migraciones no se ejecutan automáticamente. Antes de usarlas, sigue el procedimiento y las precauciones de [`docs/laboratorio/migraciones.md`](../laboratorio/migraciones.md) y [`docs/integracion/2026-11-10-resultado-integracion.md`](../integracion/2026-11-10-resultado-integracion.md). En particular, no ejecutes `alembic upgrade head` a ciegas sobre una base existente. Las migraciones deben ejecutarse con credenciales de administración, no con el rol de la aplicación.

## Cuentas autorizadas

No existe una ruta HTTP para registrarse. Un administrador autorizado puede crear cuentas desde la consola del servidor, vinculadas a un trabajador activo existente:

```sh
docker compose --env-file deploy/hospital.env -f deploy/docker-compose.hospital.yml \
  exec backend python -m app.accesos.infrastructure.provisioning \
  identificador --trabajador-id ID --rol medico --operador IDENTIFICADOR_ADMIN --referencia TICKET
```

El comando solo crea cuentas para los roles permitidos, exige un registro médico activo para el rol médico y no modifica cuentas existentes. La contraseña se solicita interactivamente y se almacena con Argon2. Protege el acceso SSH/Docker: los valores `--operador` y `--referencia` son etiquetas declaradas por quien ejecuta el comando, no una autenticación del administrador ni un registro de auditoría verificable. TI debe conservar el ticket y la salida de la operación en su sistema de auditoría. El comando de alta no reemplaza el proceso institucional para desactivar cuentas cuando una persona deja de estar autorizada.

## Datos, copias y operación

Los volúmenes `hospital_db_data` y `hospital_storage_imagenes` son persistencia local, **no copias de seguridad**. Define backups cifrados fuera del servidor para PostgreSQL y los archivos, retención aprobada y pruebas periódicas de restauración. Protege también los modelos locales y el disco del servidor. No habilites extractor clínico, visión radiológica ni servicios externos sin aprobación específica y revisión de privacidad.

El backend expone documentación API solo cuando `API_DOCS_ENABLED=true`; producción la desactiva. El endpoint de salud de base de datos queda bloqueado desde el frontend. Revisa logs, alertas, actualizaciones de imágenes y dependencias, rotación de secretos, respuesta a incidentes, límite de intentos de login y posible MFA/SSO con TI antes de permitir datos reales.

## Verificación y límites

Comprueba `docker compose ps`, `docker compose logs` y `https://<nombre-interno>/api/health` desde una estación autorizada. Prueba los seis escenarios de acceso (médico, laboratorio, enfermería y roles no permitidos), la revocación/desactivación de cuentas, los límites de carga, backups y restauración en una copia aislada.

Este Compose es una base endurecida, no una certificación. No se ha configurado el DNS, el proxy TLS institucional, el firewall, copias externas, MFA, monitoreo ni un proceso aprobado de revocación; TI del hospital debe resolver y validar esos puntos antes de usar datos reales.
