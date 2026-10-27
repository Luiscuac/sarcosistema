# Consulta Médica Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir al médico buscar pacientes, leer cualquier historial y registrar una consulta SOAP única, auditada y recuperable desde PostgreSQL.

**Architecture:** Reutilizar las tablas clínicas existentes y una revisión Alembic aditiva; módulo `app.consultas` con dominio/aplicación/infraestructura/presentación. Frontend aislado en `features/consultas` sobre autenticación, React Query y la identidad visual de Laboratorio sin tocarlo.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 async, asyncpg, Alembic, PostgreSQL, React/Vite JavaScript, Axios, React Query.

**Spec:** `docs/superpowers/specs/2026-10-27-consulta-medica-design.md`

## Global Constraints

- Trabajar en rama `features/historia_clinica` sin descartar cambios del usuario; nunca reinicializar `database/schema.sql` sobre BD con datos.
- No agregar dependencias, IA, recetas, pacientes por búsqueda ni edición de consultas históricas. No usar datos de las fotos como fixtures.
- El médico solo tiene una especialidad histórica; si hay duplicados, abortar migración sin perder datos; no borrar `fecha_fin` legado.
- Todas las lecturas y escrituras requieren rol `medico`; actor y fecha de atención del servidor. Mostrar abiertas y anuladas a todos los médicos autorizados, en lectura.
- Usar tokens y patrones visuales de Laboratorio, sin modificar lógica de Laboratorio. Si no hay Figma accesible, no atribuirle decisiones.
- Sin confirmación de éxito sin ejecución de verificaciones. Commits solo si el usuario lo solicita.

## Review Focus

1. Médico sin fila en `medico_especialidad` o con `vigente=false`: creación rechazada sin insertar consulta; probar en Task 3.
2. Misma clave UUID con diferente paciente o contenido: 409 sin filtrar historial de otro paciente; probar en Task 3.
3. Búsqueda por `%`, `_` o cadena de espacios: no debe exponer listado amplio ni consulta ilimitada; probar en Task 2.
4. Cuadro de diálogo de confirmación cancelado o navegación con cambios: no se envía ni pierde formulario sin aviso; probar en Task 4.
5. Consulta legada con `datos_clinicos_jsonb` ausente o estado `anulada`: detalle accesible para rol médico sin romper UI; probar en Tasks 2 y 4.

---

### Task 1: Migración segura de especialidad e idempotencia

**Files:**
- Create: `backend/alembic/versions/20261027_0007_consultas_medicas.py`
- Test: `backend/tests/test_migracion_consultas.py`

**Interfaces:**
- Consumes: esquema `consulta`, `medico_especialidad` y revisión `20261027_0006`.
- Produces: `medico_especialidad.vigente BOOLEAN NOT NULL`; `UNIQUE(medico_id)`; `consulta.clave_idempotencia UUID NULL`, `consulta.usuario_creacion_id BIGINT NULL` FK `usuario`, y unicidad `(usuario_creacion_id, clave_idempotencia)`; datos legados conservados.

- [ ] **Step 1: Write the failing test**: `test_migracion_rechaza_especialidades_duplicadas_sin_borrar_filas` y `test_migracion_agrega_vigencia_y_clave_sin_alterar_consultas_existentes` en base aislada/ficticia o revisión estructural si la BD no está disponible.
- [ ] **Step 2: Run test to verify it fails**: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_migracion_consultas.py -q`; expected FAIL antes de la migración.
- [ ] **Step 3: Implement `upgrade() -> None`**: validar duplicados antes de DDL; poblar `vigente` según `fecha_fin IS NULL OR fecha_fin >= CURRENT_DATE`, agregar constraints e índices sin DROP; `downgrade()` no elimina información clínica. Evitar UPDATE de `fecha_fin`.
- [ ] **Step 4: Run test to verify it passes**: mismo comando, expected PASS; `alembic upgrade head` solo en BD de desarrollo verificada y sin duplicados, previa comprobación del estado de versión.
- [ ] **Step 5: Record review checkpoint**: mostrar nombre de revisión y evidencia de preservación, no crear commit salvo autorización.

### Task 2: Búsqueda de pacientes e historial/detalle con RBAC

**Files:**
- Create: `backend/app/consultas/domain/entities.py`, `backend/app/consultas/application/ports/consulta_repository.py`, `backend/app/consultas/application/use_cases/consultar_pacientes.py`, `backend/app/consultas/application/use_cases/consultar_historial.py`, `backend/app/consultas/infrastructure/persistence/repository.py`, `backend/app/consultas/presentation/schemas.py`, `backend/app/consultas/presentation/router.py`
- Modify: `backend/app/main.py` (registro del router)
- Test: `backend/tests/test_consultas_lectura.py`

**Interfaces:**
- Consumes: `get_db()`, `requiere_rol('medico')`, `Paciente`, SQLAlchemy AsyncSession y tablas existentes.
- Produces: `GET /consultas/pacientes?buscar=&pagina=&limite=`, `GET /consultas/pacientes/{paciente_id}`, `GET /consultas/pacientes/{paciente_id}/historial?pagina=&limite=`, `GET /consultas/{consulta_id}`; paginación `{items,total,pagina,limite}`; historial ordenado fecha/id DESC, cualquier médico puede leer todos los estados.

- [ ] **Step 1: Write failing tests**: `test_busca_nombre_documento_historia_y_codigo_con_paginacion`, `test_rechaza_busqueda_vacia_y_comodines`, `test_detalle_consulta_legacy_sin_json`, `test_medico_lee_anulada_de_otro`, `test_no_medico_recibe_403_en_todas_las_rutas` y `test_id_inexistente_404` con datos ficticios.
- [ ] **Step 2: Run tests red**: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_consultas_lectura.py -q`; expected FAIL (rutas ausentes).
- [ ] **Step 3: Implement read interfaces**: `SqlAlchemyConsultaRepository(db: AsyncSession)` expone `buscar_pacientes(buscar: str, pagina: int, limite: int)`, `obtener_paciente(id: int)`, `listar_historial(paciente_id: int, pagina: int, limite: int)` y `obtener_consulta(id: int)`; usar filtros parametrizados y escapar comodines LIKE; limitar a 30/página; convertir JSON legado vacío a estructura de lectura sin alterar la BD.
- [ ] **Step 4: Run tests green**: mismo comando, expected PASS; comprobar import `app.main`.
- [ ] **Step 5: Record review checkpoint**: comprobar directamente que cada ruta deniega sin token y a roles ajenos.

### Task 3: Registro SOAP atómico, auditado e idempotente

**Files:**
- Create: `backend/app/consultas/application/use_cases/registrar_consulta.py`, `backend/app/consultas/domain/validators.py`
- Modify: `backend/app/consultas/application/ports/consulta_repository.py`, `backend/app/consultas/infrastructure/persistence/repository.py`, `backend/app/consultas/presentation/schemas.py`, `backend/app/consultas/presentation/router.py`
- Test: `backend/tests/test_consultas_escritura.py`

**Interfaces:**
- Consumes: interfaces/JSON de Task 2 y columnas de Task 1.
- Produces: `POST /consultas` acepta `paciente_id`, `clave_idempotencia: UUID`, `motivo_consulta`, `diagnostico_principal` y otros campos SOAP opcionales definidos en spec; responde detalle (`201` primera vez, `200` replay) o 409 para clave reutilizada con datos distintos. Solo identidad autenticada determina `medico_id`, `especialidad_id`, `usuario_creacion_id`, fecha; crea auditoría en misma transacción.

- [ ] **Step 1: Write failing tests**: `test_registra_persiste_audita_y_relee`, `test_reintento_misma_clave_no_duplica`, `test_reintento_distinto_con_misma_clave_409`, `test_medico_sin_especialidad_vigente_no_inserta`, `test_validacion_negativos_cero_saturacion_y_presion`, `test_campos_opcionales_null`, `test_paciente_inexistente_404`, `test_rol_laboratorio_403`, `test_medico_y_fecha_del_servidor`.
- [ ] **Step 2: Run tests red**: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_consultas_escritura.py -q`; expected FAIL.
- [ ] **Step 3: Implement `RegistrarConsulta.ejecutar(datos: ConsultaNueva, usuario_id: int) -> ConsultaDetalle`**: resolver médico desde `usuario.trabajador_id`; verificar vigente, paciente y unicidad; validar números finitos >0, saturación ≤100 y sistólica > diastólica cuando ambas presentes; insertar `consulta` y `auditoria_accion` sin commit en repositorio, reutilizar UUID; no aceptar campos de autor ni fecha; comparar payload canónico en replay y negar conflicto incluso si es otro paciente.
- [ ] **Step 4: Run tests green**: mismo comando, expected PASS; ejecutar tests de Tasks 1 y 2.
- [ ] **Step 5: Record review checkpoint**: verificar mismo paciente/id en consulta persistida e historial y auditoría sin narrativas clínicas.

### Task 4: Pantallas médicas y formulario SOAP

**Files:**
- Create: `frontend/src/features/consultas/api/consultasApi.js`, `frontend/src/features/consultas/hooks/useConsultas.js`, `frontend/src/features/consultas/pages/ConsultasPage.jsx`, `frontend/src/features/consultas/pages/consultas.css`, `frontend/src/features/consultas/components/PacienteFicha.jsx`, `frontend/src/features/consultas/components/ConsultaFormulario.jsx`, `frontend/src/features/consultas/components/ConsultaDetalle.jsx`, `frontend/src/features/consultas/utils/formulario.js`, `frontend/src/features/consultas/utils/formulario.test.js`
- Modify: `frontend/src/app/router.jsx` y `frontend/src/features/inicio/pages/InicioPage.jsx` (solo enlace médico)
- Test: `frontend/src/features/consultas/utils/formulario.test.js`; prueba de interfaz adicional si el proyecto dispone de runner DOM.

**Interfaces:**
- Consumes: endpoints/shape de Tasks 2–3, `httpClient`, `ProtectedRoute rolesPermitidos={['medico']}`, tokens CSS globales y `.primary-button`.
- Produces: `/consultas` búsqueda paginada, `/consultas/pacientes/:pacienteId` ficha e historial, `/consultas/pacientes/:pacienteId/nueva` formulario, `/consultas/:consultaId` detalle; transformación `formularioAPayload(form, pacienteId, clave)` y `calcularImc(pesoKg, tallaCm)`.

- [ ] **Step 1: Write failing tests**: `calcularImc` nulo ante valores ausentes y cálculo correcto en válidos, `formularioAPayload` envía `null` para campos vacíos y no envía médico/fecha; si hay runner DOM, verificar rechazo de doble envío, cancelación de confirmación y advertencia de salida.
- [ ] **Step 2: Run tests red**: `cd frontend; npm test -- --run` o el script real de `package.json`; expected FAIL por utilidades inexistentes.
- [ ] **Step 3: Implement UI**: usar `useQuery`/`useMutation` con invalidación tras guardar, UUID estable con `useRef(crypto.randomUUID())`, confirmación antes de POST, bloqueo de envío pendiente, `beforeunload` y guard de navegación interna por cambios, secciones SOAP etiquetadas, estados de error/vacío/carga, sidebar/topbar médicos visualmente consistentes con laboratorio y CSS acotado.
- [ ] **Step 4: Run tests green**: script real de pruebas y `npm run build`, expected PASS; comprobar teclado/responsividad y datos solo de API.
- [ ] **Step 5: Record review checkpoint**: desde login médico, recorrer búsqueda→ficha→nuevo→confirmación→detalle→historial y comprobar que laboratorio no cambió.

### Task 5: Verificación integrada y documentación operativa

**Files:**
- Create: `docs/consultas/uso-y-migracion.md`
- Modify: tests de Tasks 1–4 si exponen discrepancias reales (sin relajar assertions).

**Interfaces:**
- Consumes: Tasks 1–4 completas.
- Produces: instrucciones de migración, preparación segura de cuenta médico/especialidad ficticia y checklist de verificación real.

- [ ] **Step 1: Run backend smoke**: `cd backend; .\.venv\Scripts\python.exe -c "import app.main"`; expected exit 0, con `.env` configurado.
- [ ] **Step 2: Run backend suite**: `cd backend; .\.venv\Scripts\python.exe -m pip check` y `cd backend; .\.venv\Scripts\python.exe -m pytest`; expected PASS o documentar fallos preexistentes.
- [ ] **Step 3: Run frontend suite/build**: `cd frontend; npm run build` y script test existente; expected PASS.
- [ ] **Step 4: Verify real PostgreSQL safely**: consultar versión Alembic y duplicados sin modificar datos; aplicar upgrade solo tras preflight; probar con cuenta/paciente ficticios y comprobar persistencia, auditoría, historial, denegación de otro rol y reintento UUID. No ejecutar `schema.sql` sobre base existente ni insertar datos reales.
- [ ] **Step 5: Write documentation**: `docs/consultas/uso-y-migracion.md` con rutas, migración, estado vigente/no vigente, limitaciones, resultados medidos y punto de extensión para futura transcripción revisada (sin implementarla).

## Self-review

Cada requisito de la spec se localiza en Tasks 1–5. El flujo completa una consulta cerrada; borradores/edición/corrección permanecen explícitamente fuera de alcance. Interfaz y DB usan los mismos nombres JSON; los cinco riesgos de Review Focus están cubiertos por tests en sus tareas. No se asume que una base local permita pruebas integradas hasta comprobar su estado.
