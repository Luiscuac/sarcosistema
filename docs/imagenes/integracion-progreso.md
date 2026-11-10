# Ledger — plan: docs/superpowers/plans/2026-11-03-rayos-x-integracion.md

Ejecución directa confirmada; diseño y plan aprobados. Conservar main y cambios locales autorizados de sesiones anteriores; no commits ni push. Se mantiene ledger aquí por ser sesión Windows sin commits y trabajo ya compartido con fases previas; no se mueven ni descartan archivos locales.

Pre-flight: Task1 snapshots/autorización → Task2 ejecución y Task3 API: mismo estudio/informe/archivo y usuario servidor. Task2 estados/resultado JSON → Task3/Task4: trabajo persistido con consulta de estado. Task3 versión de revisión → Task4 envío explícito con control optimista.

- [x] Task1: persistencia, lectura autorizada y archivos seguros.
- [x] Task2: trabajos controlados y fusión conservadora.
- [x] Task3: API autenticada y revisión médica.
- [x] Task4: pantalla, demo y verificación real/browser/offline; límites y omisiones registrados.

Prerrequisito RAG cerrado: prueba offline final 5 passed en 344,22 s, red interna sin salida externa, sin OOM, según guía Fase3. No se inicia LLM ni se cargan dos modelos simultáneamente.

Avance inicial (histórico; ver el cierre al final):
- Migración 0009, repositorio autorizado, archivos con hash/tamaño/raíz, idempotencia y revisión append-only implementados con pruebas RED→GREEN. Archivo symlink omitido en Windows por privilegios: debe comprobarse en Linux/offline.
- Cola persistida con líder PostgreSQL, recuperación de interrupciones, visión y RAG secuenciales; API real bajo /imagenes con rol médico y actor servidor. Router 3 passed; trabajos y router 5 passed en verificación ligera.
- Pantalla React creada dentro del frontend existente; sidebar/topbar de Laboratorio parametrizados conservando defaults. Imagen blob autenticada, polling, scores no porcentuales, informe de solo lectura, extracción/contradicciones/citas y revisión explícita. Node tests 25 passed, lint correcto; prueba browser pendiente.
- Ruling: PostgreSQL localhost5432 cambió y rechaza la configuración local; no alterar sus claves. Base temporal propia sarco-rx-integracion-db en localhost55432, tmpfs y sin volumen clínico, bootstrap solo por ser nueva y nueve migraciones aplicadas. Coste: no certifica conectividad de la instalación del usuario en5432.
- En esa base: pruebas dirigidas de repositorio/router/trabajos 8 passed; demo nuevo creado con médico/paciente ficticios reservados sin tocar cuentas ajenas. Radiografía NIH e informe se marcan simulación, no par auténtico. Indexación del corpus real iniciada aparte; pendiente comprobar resultado.
- Ruling: perfil visual de demostración 2048 MiB solo si la RAM actual lo permite; se mantiene default4096 y embeddings2048. Margen fundamentado en RSS visual ~400MiB medida en Fase2. Coste: no extrapolar a cargas mayores; no eliminar guards.

Cierre documental retomado el 09/11/2026; no repite inferencias ni presenta los resultados históricos como ejecuciones de hoy:
- Pruebas finales antes de la pausa: backend 280 passed, 11 skipped en 64,93 s contra la base temporal propia; frontend 27 passed, lint/build correctos; pip check e import app.main correctos, sin Torch al arrancar.
- Navegador real: login, estudio, imagen, modelos reales, cuatro fuentes y rechazo explícito persistido tras recargar. Cero recursos externos de UI. Conflicto concurrente real por API con borrador base retenido; retiro de archivo simulado en GET de detalle ocultó imagen y resultado incompatible.
- API offline real: scripts.verificar_imagenes_offline terminó correctamente en red Docker --internal con PostgreSQL temporal, pesos/corpus/archivo readonly y cuota 3GiB. Comprobó bloqueo externo real del SO, visión/RAG reales, cuatro citas, idempotencia, revisión persistida/409 y conservación literal del informe. Visión 0,995 s pase, 27,714 s completos, RSS observada 456.507.392 bytes. No confundir cuota con pico de RAG ni harness API con navegador en contenedor.
- Final: fixed negaciones/incertidumbre — cuatro regresiones RED→GREEN en test_fusion_hallazgos; fallo BD RAG — test_fallo_bd_rag_conserva_vision_valida RED→GREEN.
- Final: fixed liderazgo — tests de pérdida de vigencia y fence SQL RED→GREEN, más terminación real de conexión PostgreSQL propia. Claim/recuperación atados a conexión del lock; monitor y finalización cercada por PID/backend_start.
- Final: fixed snapshot UI y versión del borrador — helpers RED→GREEN y pruebas browser de conflicto/snapshot. Imagen retirada también oculta; no se deja resultado junto a otra versión.
- Final: minor (deferred): symlink en Linux no ejecutado; Windows omitió por privilegios. El harness offline no afirma cubrir ese caso.
- Guía final: docs/imagenes/integracion-local.md; README actualizado. Sin commits/push ni modificación de claves/.env del usuario.
- Entorno actual: Docker Desktop Linux no disponible al inspeccionar el 09/11 (pipe no encontrado). No se reinició ni se recreó el entorno. La integración está implementada y tiene evidencia anterior; para usarla ahora se requiere iniciar Docker/BD y validar configuración local. No asumir persistencia de bases tmpfs tras reinicio.
- Verificación del cierre documental: ejemplos PowerShell parseados sin ejecutar arranques; `git diff --check` con la configuración normal del repositorio terminó sin errores (avisos LF/CRLF). No hay nueva afirmación de suite verde actual ni autorización para merge/commit/push; se conserva feat/rayos-x y todos los archivos locales.
