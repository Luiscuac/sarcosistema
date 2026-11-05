# Revisión y correcciones — 29/10/2026

## Alcance y método

Rama de partida `main`, árbol limpio. Se revisaron composición y configuración, acceso/JWT, consultas e historial, extracción clínica, frontend de sesión y audio, persistencia/validaciones de Laboratorio, CI, documentación de inicio y el agente Windows independiente. La petición de revisar el proyecto no se interpreta como autorización para eliminar información, cambiar reglas clínicas, rediseñar módulos o afirmar ausencia absoluta de errores.

Línea base reproducida: **143 pruebas backend y 19 frontend aprobadas**, lint correcto. Los fallos de esta revisión son casos que esa línea base no cubría. Cada corrección funcional tiene una prueba que reprodujo el problema antes del cambio.

## Correcciones

| Área | Fallo reproducido | Corrección y prueba |
|---|---|---|
| Acceso | JWT firmado sin `exp`, o con sujeto que no era texto, se aceptaba | Claims `exp` y `sub` obligatorios y sujeto string. `app/accesos/tests/test_jwt_service.py`: RED 9 fallos → GREEN 11 casos. |
| Sesión frontend | React Query conservaba información clínica al salir o cambiar de cuenta | Vaciar/cancelar caché en login/logout; callbacks estables. `sesion.test.js`: caché vacía incluso si una petición antigua termina después. |
| Pacientes | Documentos hechos de espacios se aceptaban y espacios laterales cambiaban la identidad | Normalizar antes de validar; rechazar documentos vacíos y nacimiento futuro; preservar identificadores opcionales válidos. |
| Búsqueda Laboratorio | `%` y `_` se interpretaban como comodines, y un término en blanco ampliaba resultados | Búsqueda literal escapada y término vacío sin consulta. Pruebas ejecutan SQL contra filas ficticias en SQLite, sin modificar la BD clínica. |
| Reenvío de solicitud | La misma clave con prioridad, profesional, diagnóstico, establecimiento, formulario, fecha explícita o actor diferentes devolvía la solicitud anterior | Comprobar todos los campos enviados y autor antes de devolver un replay. El reloj generado por servidor **no** invalida un reintento si el cliente omitió fecha: el router conserva ese dato de procedencia, sin nueva columna. |
| IA: ambigüedad excesiva | “Niega fiebre…, temperatura 36.5…, peso 75…” marcaba las mediciones como inciertas por una negación ajena | Limitar contexto de negación/fecha al fragmento de la medición explícita. No se habilita aceptar una propuesta genuinamente ambigua. |
| IA: medidas | “Peso 75 kilos y temperatura 39, perdón, 37…” podía proponer peso 37; Fahrenheit se interpretaba como Celsius | No resolver automáticamente correcciones que mezclan medidas; no considerar Fahrenheit como °C. No se calculan conversiones clínicas no autorizadas. |
| Proveedor IA | `content:null` o lista provocaban `AttributeError` y error 500 | Validar estructura antes de usar texto; error recuperable genérico sin datos clínicos. |
| Historial | JSON histórico de tipo lista/escalar o cadena incompatible hacía fallar toda la lectura | Conservar metadatos/identidad de consulta y advertir explícitamente incompatibilidad. No alterar ni borrar el dato original. |
| Audio | El evento `onstop` tardío, después de detener y cancelar, iniciaba transcripción | Invalidar callbacks y comprobar generación/montaje; detener también el medidor tardío. Prueba de navegador falló antes y pasó después. |
| Docker | El backend heredaba `DATABASE_URL` con `localhost`, que dentro del contenedor no es PostgreSQL | Compose usa hostname interno `db`. Prueba resuelve `docker compose config` sobre `.env` ficticio y verifica el destino, sin iniciar ni borrar servicios. |
| Documentación | Inicio sugería `src.main`, migraciones opcionales y otro motor Whisper | README corregido a `app.main`, Alembic obligatorio y faster-whisper. |

## Archivos principales

- Backend: JWT; `laboratorio/{presentation,application,domain,infrastructure}`; extracción y adaptador Ollama de `consultas`; presentación de consultas históricas en su repositorio.
- Frontend: `AuthContext.jsx`, nueva utilidad `sesion.js`, `ConsultaDetalle.jsx`, `useAudioRecorder.js` y prueba de navegador `frontend/tests/consulta-ia.browser.js`.
- Regresiones nuevas: `app/accesos/tests/test_jwt_service.py`, `app/laboratorio/tests/test_regresiones_pacientes_solicitudes.py`, `app/consultas/tests/test_regresiones_revision.py`, `app/config/tests/test_compose.py`, `frontend/src/features/accesos/auth/sesion.test.js`.
- Configuración/documentación: `docker-compose.yml`, `README.md`, este informe. No nuevas migraciones, dependencias ni cambios de datos persistentes.

## Verificación y límites

- La prueba de navegador utiliza componentes y rutas reales con respuestas ficticias controladas: cambio de paciente, protección de cambios manuales, cancelación de inferencia, recuperación manual ante error de IA, permiso de micrófono tardío y audio tardío tras cancelar. No guarda consultas.
- Las pruebas de PostgreSQL existentes usan rollback; no se reinicializó `schema.sql` ni se borraron volúmenes. La prueba de Docker es de configuración, **no** certifica que se haya construido y desplegado toda la imagen.
- El agente Windows depende de una aplicación y controles externos: no se ejecutó automatización sobre ventanas de trabajo del usuario ni sobre el sistema hospitalario antiguo.
- Una prueba verde y esta revisión no son validación clínica ni garantía de ausencia de otros bugs. El caso exacto de ambigüedad reportado por el usuario sigue necesitando un ejemplo ficticio si ocurre con otro texto; no se retiraron barreras para aceptar datos inciertos.
- Para usar los cambios del backend ya iniciado, detenerlo con Ctrl+C y volver a iniciarlo; al cambiar de rama no confiar únicamente en reload.

Resultados finales y revisión independiente se anotarán al terminar la ejecución.
