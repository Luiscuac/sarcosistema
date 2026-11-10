# Integración Rayos X Implementation Plan

Estado de entrega: implementación y verificaciones previas registradas en `docs/imagenes/integracion-progreso.md`; cierre documental el 09/11/2026. Guía de uso y límites: `docs/imagenes/integracion-local.md`. No repetir tareas ya verificadas ni asumir entorno activo: Docker no estaba disponible al retomar el cierre. Rama conservada sin merge, commit ni push.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrar visión y RAG locales con revisión médica explícita dentro de SarcoSistema.
**Architecture:** Módulo imagenes con dominio, puertos, casos de uso, repositorio SQLAlchemy y router FastAPI. Trabajos persistidos y controlados ejecutan visión y embeddings secuencialmente; React reutiliza el diseño de Laboratorio y la sesión existente.
**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async, Alembic, PostgreSQL16/pgvector, React/Vite, React Query, node:test, pytest y pruebas browser.
**Spec:** `docs/superpowers/specs/2026-11-03-rayos-x-integracion-design.md`

## Global Constraints
- Sin entrenamiento, LLM nuevo, proveedores externos en runtime ni diagnósticos automáticos.
- No sobrescribir cambios locales, cuentas ni datos existentes; sin commits/push.
- Archivos PNG/JPEG locales bajo raíz configurada, hash y autorización obligatorios.
- Informe publicado en modo lectura; revisiones de IA separadas y explícitas.
- Solo médico solicitante autorizado; acceso directo por id también se valida.
- Una inferencia por entorno, visión/embeddings secuenciales, memoria y timeout.
- Datos ficticios o de investigación; cualquier emparejamiento artificial se marca simulación.

## Review Focus
- Archivo retirado, reemplazado o versión de informe cambiada entre solicitar y ejecutar: rechazar snapshot obsoleto.
- Reinicio, timeout y doble envío: no dejar trabajos procesando indefinidamente ni duplicar inferencia.
- Ruta externa/traversal/symlink y permisos por id: no filtrar archivos ni datos de otro médico.
- Negación, incertidumbre y scores: no promover resultados técnicos a diagnóstico ni resolver contradicciones.
- Revisión concurrente: conservar historial, actor servidor y evitar sobrescrituras.

### Task 1: Persistencia y lectura autorizada
**Files:** crear `backend/alembic/versions/20261103_0009_analisis_imagenes.py`, `backend/app/imagenes/domain/analisis.py`, `application/ports/estudios.py`, `infrastructure/persistence/repository.py`, `infrastructure/archivos.py`, `tests/test_estudios_imagenes.py`.
**Interfaces:** `EstudiosRepository.listar(usuario_id, pagina)`, `obtener(estudio_id, usuario_id)`, `crear_analisis(snapshot, usuario_id, clave)`, `obtener_analisis(id, usuario_id)`, `registrar_revision(id, usuario_id, version, decision, motivo, correccion)`; archivo seguro devuelve bytes y MIME sin exponer path.
- [ ] Revisar constraints/triggers de las tablas originales y auth; pruebas RED de acceso propio/ajeno, borrador oculto, archivo retirado y traversal/symlink/hash incorrecto.
- [ ] Crear migración incremental de análisis y revisiones con FK/estados/clave idempotente/versión, sin alterar informe ni diagnóstico. Implementar lecturas parametrizadas y archivos limitados a raíz local.
- [ ] Probar PostgreSQL real con rollback, reintento compatible/incompatible, revisión concurrente e inmutabilidad clínica; ejecutar GREEN.

### Task 2: Análisis controlado y fusión conservadora
**Files:** crear `application/analizar_estudio.py`, `application/fusionar_hallazgos.py`, `infrastructure/trabajos.py`, `infrastructure/rag/servicio.py`, `tests/test_analisis_estudio.py`, `tests/test_fusion_hallazgos.py`; adaptar composición existente sin imports pesados de arranque.
**Interfaces:** `AnalizarEstudio.ejecutar(analisis_id)` produce JSON experimental con visión, informe_original, extracción con evidencia, discrepancias y RAG; `Trabajos.solicitar` devuelve id/estado, recupera interrupciones y limita concurrencia.
- [ ] RED: negaciones/posible/ambiguo, discrepancia sin diagnóstico, modelo/RAG ausente, snapshot cambiado y dos envíos simultáneos.
- [ ] Ejecutar modelos existentes secuencialmente fuera del event loop; workers efímeros, timeout y errores seguros. Consultar corpus preparado desde adaptador de aplicación, no importar scripts CLI en runtime.
- [ ] Persistir finalización/fallo con transacciones cortas y recuperación tras reinicio; no mantener sesión clínica abierta mientras inferencia carga. GREEN con dobles de puertos y una prueba real optativa.

### Task 3: API y revisión médica
**Files:** crear `presentation/router.py`, `presentation/schemas.py`, `tests/test_router_imagenes.py`; modificar `backend/app/main.py`, `.env.example` para configuración sin secretos reales.
**Interfaces:** GET `/imagenes/estudios`, GET `/imagenes/estudios/{id}`, GET archivo autorizado; POST `/imagenes/estudios/{id}/analisis`, GET `/imagenes/analisis/{id}`, GET fuentes locales, POST revisión con versión esperada.
- [ ] RED con dependencias sobrescritas: 401/403/404 por id, 409 idempotencia/versionado, 422 validación y 503 recursos; comprobar no filtrar rutas ni errores internos.
- [ ] Reutilizar usuario_actual/requiere_rol y get_db; actor servidor, revisión append-only con motivo al corregir/rechazar. Wirear router y ciclo de trabajos, mantener backend manual funcional sin modelos.
- [ ] GREEN de API y persistencia: el mismo usuario no puede cambiar actor ni auto-publicar un informe a través del análisis/revisión.

### Task 4: Pantalla, demostración y verificación final
**Files:** crear `frontend/src/features/imagenes/{pages/ImagenesPage.jsx,components/EstudioDetalle.jsx,api/imagenes.js,analisis.js,analisis.test.js}`, estilos mínimos; modificar `frontend/src/app/router.jsx` y acceso Inicio; crear `backend/scripts/preparar_estudio_imagen_demo.py`, `frontend/tests/imagenes.browser.js`, `docs/imagenes/integracion-local.md`.
**Interfaces:** listado/detalle y polling por análisis, imagen obtenida como blob autenticado, fuentes locales con citas, formulario de revisión con decisión/motivo/corrección y versión.
- [ ] RED node:test para estados, negaciones visibles, borrado de datos al cambiar estudio/sesión y revisión explícita. Crear layout consistente con Laboratorio sin duplicar su lógica clínica.
- [ ] Preparar solo datos demo nuevos sin renovar cuentas; marcar simulación si informe e imagen no son un par auténtico. Probar browser con backend real y autorización, error de modelo y revisión persistida.
- [ ] Verificar flujo real sin salida Internet con artefactos locales; medir memoria/tiempo y distinguir dobles de modelos reales. Revisar no modificación de diagnóstico/informe y comportamiento ante RAG insuficiente.
- [ ] Ejecutar pytest/pip check/import, npm test/lint/build, revisión independiente final y corrección RED→GREEN de hallazgos importantes. Documentar omisiones, límites y comandos; detenerse al finalizar esta entrega.

## Dependencias entre tareas y revisión del plan
Task1 produce snapshots/lecturas autorizadas para Task2 y Task3; Task2 produce estados/JSON para Task3; Task3 define API usada por Task4. La revisión validará firmas y claves antes de cada implementación. Cada clase de Review Focus tiene pruebas asignadas a Task1–3. El diseño fue revisado por un builder independiente sin preguntas importantes pendientes. La Fase3 offline final es prerrequisito, no se la presume aprobada. Este plan no autoriza operaciones destructivas ni publicación.
