# Integración local de Laboratorio, Ecografía y Rayos X

## Alcance y seguridad

Trabajo en `integracion/main-rayos-x-20261109`, worktree aislado existente.
Referencia integrada: `origin/main` en `50c797b`; feature original `5d92041`.
Respaldo conservado: `backup/rayos-x-pre-integracion-20261109-5d92041`.
No push, cambios a main, reset, clean, stash, stamp, downgrade ni migraciones
sobre la base real. El checkout original se conserva separado.

Esta evidencia es nueva de la sesión de integración, no reutilizada de auditorías
anteriores. Solo se usaron bases nuevas con datos ficticios y una muestra pública
NIH preparada previamente con su manifest; el informe asociado declara simulación.

## Estrategia Alembic

Se descartó restaurar el padre original como única solución: las instalaciones
que ya aplicaron el grafo reordenado de main intentarían repetir DDL de Laboratorio.
Se conserva exactamente el padre distribuido en main para `20261103_0008`:
`20261104_0012`. Los cuerpos de las migraciones históricas no se reescriben.
La migración de Ecografía se incorporó idéntica a main, no se eliminó ninguna.

Nueva revisión `20261109_0013`, hija de la unión `20261109_0012`:

- Comprueba físicamente columnas y contrato de Laboratorio0008.
- Si faltan los formatos0009, ejecuta la operación original que crea nuevas
  versiones sin reescribir resultados históricos. Si existen, comprueba una
  versión histórica completa (campos, unidades, referencias y opciones), sin
  reemplazar la versión activa personalizada por una instalación.
- Comprueba o incorpora responsables/incidencias0010 y estados/vista0011.
- Repite únicamente el INSERT anti-duplicados original del catálogo Ecografía:
  conserva identificadores, nombres personalizados, activación y filas existentes.
- No recrea tablas IA/RAG ni elimina datos o extensión vector.
- Contratos parciales/incompatibles conocidos abortan y revierten la transacción.
- Downgrade bloqueado. No se modifica manualmente `alembic_version`.

### Dos cabezas originales IA + Laboratorio

El grafo reordenado no puede planificar esos dos heads: se solapan. El preparador
`backend/scripts/reconciliar_historial_imagenes.py` detecta pares reconocidos de
IA0008/0009 y Laboratorio0008/0009/0010/0011. Construye una copia temporal del
grafo original (solo cambia el padre de RAG en esa copia), completa las operaciones
pendientes hasta la unión0012 mediante Alembic y después actualiza al head actual.
No hace stamp, no inventa filas de tracking ni edita archivos históricos del repo.

Inspección y dos etapas comparten **una conexión y una transacción externas**.
`env.py` respeta la conexión proporcionada y la URL explícita de Config; no usa
otra URL de settings para ejecutar las operaciones. Ante fallo de la correctiva,
también se revierten DDL/DML y tracking de la unión histórica. Las secuencias
PostgreSQL pueden consumir valores incluso al revertir transacciones, como es
habitual; no se promete ausencia de huecos. Historiales múltiples desconocidos
se rechazan. Una regresión prueba rollback desde dos heads con esquema incompatible.

### Procedimiento para una instalación existente (NO ejecutado sobre la real)

1. Respaldar y obtener **solo** revisiones y metadatos técnicos; no compartir
   contraseñas, hashes, JWT ni información clínica.
2. Ensayar la copia aislada con el preparador, revisar SQL/contrato/datos y
   comprobar módulos antes de autorizar otra instalación.
3. Desde backend, `python -m scripts.reconciliar_historial_imagenes` es solo lectura.
4. `python -m scripts.reconciliar_historial_imagenes --aplicar` ejecuta los upgrades;
   usarlo únicamente en el destino aislado comprobado y autorizado. **No es una
   autorización para ejecutar ahora ese comando en la base real.**
5. Una base nueva recibe bootstrap una sola vez y luego `alembic upgrade head`.

### Matriz de actualización real

Pruebas: `backend/tests/test_integracion_historiales.py`.
Servidor propio `sarco-integracion-20261109-matrix`, PostgreSQL16/pgvector,
datos tmpfs, puerto aleatorio publicado solo en loopback `58140`.
No se montaron volúmenes ni directorios de la base original.
Cada caso crea una BD `integration_<uuid>` nueva desde schema.sql y aplica el
historial anterior mediante migraciones reales, nunca stamp.

Trece orígenes:

1. Bootstrap vacío.
2. Laboratorio0008, 0009, 0010 y 0011 (cuatro casos).
3. IA original0008 y 0009 (dos casos).
4. Unión original0012.
5. Dos heads originales IA0009+Laboratorio0008 y IA0009+Laboratorio0011.
6. main Ecografía0012, RAG0008 e IA0009 (tres casos).

Se compara entre perfiles el contrato de columnas, restricciones, índices,
vistas y triggers. Se conservan registros ficticios de paciente, solicitud,
estudio, informe publicado, archivo, documentos/fragmentos RAG, análisis y
revisión médica presentes antes del upgrade. Se comprueban los ocho tipos de
Ecografía, formatos de Laboratorio, cinco tablas nuevas y distancia vectorial
real; repetir upgrade no cambia esquema ni versiones de plantillas.

Los casos incompatibles prueban error y rollback: columna parcial, formato parcial,
nullability inválida, unidad histórica incompatible, pérdida del trigger append-only,
nullability de incidencia y pérdida de FK RAG. Además se prueban destino explícito
con el env.py real y rollback conjunto desde dos heads. La planificación comprueba
que correctiva0013 se programa desde las revisiones IA relevantes.
Total matriz/grafo/precondiciones: **23 aprobadas**.

La correctiva contrasta también huellas normalizadas del contrato PostgreSQL16
de las cinco tablas nuevas (columnas/tipos/nullability/defaults/identidad, PK/FK/
checks, índices y triggers con sus funciones). Los valores esperados provienen de
las migraciones históricas ejecutadas en la referencia aislada, sin OIDs ni datos.
Una restauración parcial no queda aceptada solo porque existan los nombres de tablas.

No es una certificación de cualquier esquema modificado manualmente: si una
instalación difiere de estos historiales, detenerse y comparar su copia aislada.

## Conflictos y conservación de funcionalidades

| Conflicto | Resolución |
| --- | --- |
| Backend `imagenes/presentation/router.py` modificado/eliminado | Se conserva la composición de main `router_clinico.py`, `router_analisis.py` y descargas. Se trasladan los campos del snapshot de feature al router de análisis; no se registra el router viejo duplicado. |
| Frontend `app/router.jsx` | Se conservan todas las rutas de Laboratorio/Consultas de main; Ecografía en `/imagenes`, rol `imagenes`; IA médica en `/imagenes/rayos-x`, rol `medico`. |
| `ImagenesPage.jsx` agregado/agregado | Bandeja de Ecografía conservada; implementación médica de feature trasladada a `RayosXPage.jsx`. |
| `imagenes.css` agregado/agregado | Estilos main intactos; estilos de feature en `rayos-x.css`, prefijos `rx-*`. |
| `LaboratorioSidebar.jsx` modificado/eliminado | Se respeta su eliminación en main. Rayos X usa navegación propia y el layout/topbar actual, sin resucitar el componente obsoleto. |
| `LaboratorioTopbar.jsx` | Contrato main con logout conservado; título opcional con default Laboratorio para reutilización desde IA. |

Revisados merges automáticos:

- `app/main.py` conserva routers de Laboratorio, médico, Consultas, accesos e IA,
  composición única de imágenes y lifespan de trabajos de feature.
- Repositorio de imágenes conserva la clase clínica y la clase de análisis,
  análisis reciente, liderazgo y fencing al finalizar trabajos.
- Se resolvió una colisión semántica: `ports.py` ocultaba `ports/vision.py`.
  El contrato clínico pasa a `ports/__init__.py`, conservando ambos imports.
- Cliente API IA y scripts de prueba offline/concurrencia actualizados al
  namespace `/imagenes/analisis/estudios`; rutas clínicas no sustituidas.
- Settings y Compose conservan campos de Ecografía, volumen de archivos y
  PostgreSQL pgvector. Dependencias y lockfile sin actualizaciones innecesarias.
- Cambios restantes de main en Laboratorio, Consultas, extracción, dictado y
  transportador se conservan; no se refactorizaron fuera de la integración.

## Pruebas ejecutadas con el código combinado

| Verificación | Resultado |
| --- | --- |
| Python3.12.10: import app.main | Correcto; Torch no importado al arrancar módulos manuales. |
| pip check | Sin requisitos incompatibles en el entorno usado. |
| pytest completo con RUN_MIGRATION_MATRIX=1 y BD aislada, después de corregir revisión | **398 passed, 11 skipped**, 184.70s. |
| RAG DB en proceso separado, RUN_RAG_DB_TESTS=1 | **3 passed**, 0.24s. |
| npm test, Node24.14.0/npm11.9.0 | **35 passed**, sin omisiones. |
| npm run lint | Correcto. |
| npm run build | Correcto. |
| Navegador Playwright + API/BD reales | Login de tres roles, Rayos X con imagen real, Consultas, solicitud/bandeja de Ecografía y formulario de Laboratorio; cero errores JS y cero recursos externos intentados. |

La suite incluye dos nuevas pruebas HTTP con login JWT real, SQLAlchemy/
PostgreSQL reales y almacenamiento temporal (sin dobles de repositorios):
Ecografía solicitud → borrador oculto → publicación → historial → descarga;
Laboratorio solicitud → muestra → borrador oculto al médico → publicación →
consulta médica. Prueban también separación de roles. Las transacciones se revierten.

La prueba de navegador no ejecutó inferencia: ésta se comprobó separadamente en
el entorno offline descrito abajo. El proxy de `vite.integracion.config.js` usa
5187/8017 para no alterar los servidores ajenos del checkout original ni CORS.

### Inferencia e integración offline reales

Contenedor propio PostgreSQL `sarco-integracion-20261109-offline` con
**`--network none`**, sin puerto publicado, BD nueva `fase5_integracion`.
El proceso de prueba comparte únicamente ese namespace de red. Imagen de entorno
ya disponible `sarcosistema-evaluacion:fase5`, con código **actual del worktree**
montado readonly; modelos/corpus/muestra originales montados readonly.
No se usó el código antiguo incorporado en la imagen para los módulos probados.

En esta sesión se aplicaron migraciones, crearon datos ficticios, indexaron dos
documentos mediante embeddings reales y ejecutó `scripts.verificar_imagenes_offline`:

- Salida a Internet realmente bloqueada, no solo una variable offline.
- API autenticada, archivo local comprobado e inferencia TorchXRayVision CPU real.
- Tres scores experimentales calculados (no diagnósticos).
- Recuperación pgvector/RAG con **4 citas** locales.
- Trabajo de análisis persistido y reintento idempotente.
- Revisión médica persistida, versión1; reintento obsoleto devuelve409.
- Texto del informe clínico publicado idéntico antes/después.

No se ejecutó Ollama/Whisper real ni se afirma su validación end-to-end. Las once
omisiones de la suite son: symlinks Windows (1), SIGTERM POSIX (1), prueba local
de pesos (1), pruebas offline optativas RAG (2) y visión (3), RAG DB optativa (1),
Ollama real (2). RAG DB se ejecutó después en proceso separado y la integración
offline real se ejecutó por su script propio; no se afirma que esos archivos
optativos de pytest se ejecutaran. Los tests con dobles mantienen su alcance.

## Secretos y artefactos

`.env` raíz confirmado como configuración local: desversionado con copia local
conservada, `.gitignore` ampliado y `.env.example` sin valores reales.
También se retiran del índice, no del disco, bytecode, temporal de main y
artefactos de `.playwright-mcp/`. Modelos, datos, logs y configuración privada
de pruebas permanecen fuera de Git.

La eliminación del índice **no borra los secretos del historial remoto**.
Tratar la clave JWT previamente versionada como expuesta si se usa en alguna
instalación: su responsable debe rotarla e invalidar sesiones. Revisar también
las credenciales de conexión que realmente se hayan usado. No se revelaron ni
rotaron valores, ni se reescribió el historial.

## Estado de entrega

La revisión independiente encontró tres problemas importantes nuevos: discrepancia
entre URL inspeccionada/ejecutada, falta de atomicidad de las dos etapas y validación
incompleta de protecciones históricas. Se reprodujeron con cinco casos RED, se
corrigieron y se verificaron GREEN junto con la suite completa. No hubo una
segunda revisión independiente: el cierre de los hallazgos se verificó con pruebas.

También señaló una política amplia preexistente en main: un médico puede descargar
archivos de estudios publicados sin comprobación adicional del solicitante en
`backend/app/imagenes/presentation/descargas.py`. Se conserva ese contrato de main;
el análisis IA sí continúa limitado al médico solicitante. **Pendiente de decisión
del equipo:** confirmar si Ecografía publicada se comparte entre todos los médicos
o requiere ownership/permiso adicional. No se cambió silenciosamente esa política.

La inferencia offline se repitió después de las correcciones de revisión en una
segunda base nueva `fase5_integracion_final`. El primer intento fue bloqueado por
`RecursosInsuficientes`: la matriz acumulaba 2.14GiB de bases tmpfs. Se respaldó
la base ficticia integration_suite (dump custom/listado fuera de Git) y se detuvo
exclusivamente el contenedor propio de la matriz. Sin cambiar umbrales ni modelos,
el nuevo intento completó inferencia, cuatro citas y revisión persistida; memoria
libre previa al modelo: 5,859,401,728 bytes. El fallo de recursos no se ocultó.

Estado técnico: integración local probada, sin conflictos de código pendientes.
Publicación: **no realizada**. Antes de solicitarla, revisar la política de descarga
anterior y la rotación de secretos históricos utilizados. No se autoriza aplicar
migraciones sobre la instalación real: necesita su ensayo y autorización separados.
La entrega posterior debe ser rama/PR hacia main, no push directo.

### Archivos principales de la resolución (además de cambios de colaboradores)

- `backend/alembic/env.py`: destino explícito y transacción externa.
- `backend/alembic/versions/20261109_0013_reconciliar_operaciones_omitidas.py`.
- `backend/scripts/reconciliar_historial_imagenes.py`.
- `backend/tests/test_integracion_historiales.py` y test de historial unificado.
- `backend/app/imagenes/application/ports/__init__.py` y retiro de ports.py.
- `backend/app/imagenes/presentation/router_analisis.py` y retiro del router viejo.
- `backend/app/imagenes/tests/test_integracion_modulos.py` y
  `test_flujos_integrados_postgres.py`.
- `backend/scripts/verificar_imagenes_offline.py`.
- `frontend/src/app/router.jsx`, página de inicio y topbar de Laboratorio.
- `frontend/src/features/imagenes/pages/RayosXPage.jsx`, `rayos-x.css`,
  `ImagenesPage.jsx`, `imagenes.css` y `api/imagenes.js`.
- `frontend/tests/imagenes-conflictos.browser.js`,
  `frontend/tests/integracion-navegacion.browser.js` y configuración Vite aislada.
- `.gitignore`, `.env.example`, README, AGENTS y documentos de integración.
- `.env`, `.pyc`, temporal y artefactos Playwright retirados solo del índice.

Inventario completo verificable: `git diff --name-status 50c797b HEAD` una vez
creado el commit final. Diferencias heredadas de whitespace en archivos de main
aparecen al comparar contra feature; no se refactorizaron. La comparación de
cambios propios contra origin/main pasa `git diff origin/main --check`.
