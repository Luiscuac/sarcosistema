# Integración main / Rayos X: detenida por seguridad

> Informe histórico de la primera auditoría. Continuación autorizada y evidencia
> nueva: [resultado de integración](2026-11-10-resultado-integracion.md).
> Los resultados y el estado detenido que siguen corresponden a la primera sesión,
> no al estado posterior de la rama de integración.

## Estado y alcance

No es un merge terminado ni una validación funcional de los tres módulos.
Se detuvo antes de `git merge`, conforme a la instrucción de no continuar ante
conflictos que no puedan resolverse con seguridad. No se modificó código,
migraciones, bases de datos, credenciales ni ramas de colaboradores.

- Origen: `feat/rayos-x`, commit `5d92041`.
- Respaldo: `backup/rayos-x-pre-integracion-20261109-5d92041` en `5d92041`.
- Referencia remota tras `git fetch origin`: `origin/main`, `50c797b`.
- Ancestro común: `6283912c7455a898e0a2464aebc4a925ddb67518`.
- Rama de diagnóstico: `integracion/main-rayos-x-20261109`.
- Workspace aislado: creado mediante la herramienta nativa de worktrees.
- Checkout original: limpio, sin merge, rebase ni cherry-pick en curso.
- No había cambios locales, archivos nuevos ni contenido preparado en el índice.
- No se usó stash, reset, restore, clean, downgrade ni push.

`main` ya incorporó la IA anterior mediante `50c797b`, pero no el último
commit `5d92041`. Desde el ancestro común: feature agrega 49 archivos y modifica
19; main agrega 88, modifica 57, elimina 6 y renombra 1. Son cambios de Git,
no un conteo de funcionalidades.

## Bloqueo reproducido: una sola cabeza puede omitir Ecografía

`backend/alembic/versions/20261103_0008_rag_torax.py` tiene la misma revisión
`20261103_0008` en ambos lados, pero distinto padre:

| Rama | down_revision |
| --- | --- |
| feature / revisión histórica original | `20261027_0007` |
| main, modificado en `50c797b` | `20261104_0012` |

La migración de Ecografía `20261104_0012` depende de Laboratorio
`20261103_0011` e inserta ocho tipos de estudio si no existen.
La revisión de unión existente de feature `20261109_0012` depende de
`('20261103_0011', '20261103_0009')` y no ejecuta DDL.

Se simuló el merge con `git merge-tree --write-tree HEAD origin/main`, sin
cambiar el índice ni el árbol de trabajo. Su código de salida fue 1 por los
seis conflictos de código listados abajo. El árbol provisional de diagnóstico
fue `80421cb1ef8e7acaba6000efe63e4435e6cc820a`; NO es un resultado publicable.

Se copiaron exclusivamente sus migraciones a un directorio temporal externo
y se consultó el plan de Alembic, sin conectar a PostgreSQL:

```text
heads = ['20261109_0012']
20261109_0012 <- ('20261103_0011', '20261103_0009')
20261103_0009 <- 20261103_0008
20261103_0008 <- 20261104_0012
20261104_0012 <- 20261103_0011

upgrade desde 20261103_0009: [20261109_0012]
upgrade desde 20261109_0012: []
```

**En ninguno de esos dos casos se programa Ecografía.** La reasignación del
padre hace que Alembic la considere un ancestro ya aplicado, aunque una base
migrada con el historial original puede no tener su catálogo. La documentación
local de reconciliación registra precisamente una instalación en `20261109_0012`;
no se consultó ni se asumió su estado actual.

No basta con contar heads ni con ejecutar las pruebas actuales del historial:
esas pruebas no comprueban la ruta de actualización hacia Ecografía desde una
base ya migrada de IA. Tampoco es seguro corregir tracking con `stamp` a ciegas.

### Decisión necesaria antes de continuar

Confirmar qué historial se distribuyó/aplicó entre colaboradores y aprobar una
estrategia de reconciliación. Una opción a evaluar es restaurar excepcionalmente
el padre histórico original de RAG, conservar todos los demás archivos y crear
una nueva unión entre `20261109_0012` y `20261104_0012`. **No se implementó**:
debe probarse también desde las bases que ya aplicaron el historial reordenado
de main, porque su tracking puede requerir reconciliación verificada para no
repetir DDL de Laboratorio. Una migración correctiva aditiva es otra opción,
pero debe demostrar que no deja objetos omitidos ni repite DDL en ningún origen.

Solicitar únicamente los identificadores de `alembic current/heads/history` y
metadatos de esquema necesarios, nunca credenciales ni datos clínicos. Probar
en bases vacías ficticias y copias aisladas autorizadas de cada estado relevante;
revisar SQL, integridad, catálogo, pgvector y conservación de datos. No aplicar
nada sobre instalaciones existentes hasta tener esa evidencia.

## Seis conflictos reales detectados y resolución propuesta

Todavía NO resueltos; detectados mediante merge-tree, sin dejar un merge activo.

| Archivo | Tipo | Integración semántica necesaria |
| --- | --- | --- |
| `backend/app/imagenes/presentation/router.py` | modificación/eliminación | main separó clínica y análisis. Trasladar los trabajos asíncronos y mejoras del router de feature a `router_analisis.py`; conservar `router_clinico.py`, descargas y composición única en `app/imagenes/router.py`. No registrar ambos routers viejos y nuevos. |
| `frontend/src/app/router.jsx` | contenido | Conservar todas las rutas de detalle, áreas, informe de Laboratorio y consulta de resultados médicos. Separar acceso médico a IA y acceso del rol `imagenes` a Ecografía, con rutas y permisos explícitos. |
| `frontend/src/features/imagenes/pages/ImagenesPage.jsx` | agregado/agregado | Son dos pantallas distintas: bandeja clínica de Ecografía y análisis de Rayos X. Conservar ambas en componentes/páginas separados, no sustituir una por otra. |
| `frontend/src/features/imagenes/pages/imagenes.css` | agregado/agregado | Conservar estilos de ambas pantallas, con ámbitos separados para impedir colisiones. |
| `frontend/src/features/laboratorio/components/LaboratorioSidebar.jsx` | modificación/eliminación | main eliminó el componente al cambiar su navegación; feature lo reutiliza para IA. Mantener la nueva navegación de Laboratorio y proporcionar navegación propia a Rayos X, sin resucitar dependencias obsoletas en Laboratorio. |
| `frontend/src/features/laboratorio/components/LaboratorioTopbar.jsx` | contenido | Mantener el contrato actual de Laboratorio y adaptar el uso desde IA sin perder compatibilidad de propiedades ni presentación. |

## Riesgos semánticos sin conflicto textual

- `backend/app/imagenes/infrastructure/persistence/repository.py`: se combina
  automáticamente, pero requiere comprobar ambos repositorios, ownership,
  publicación, idempotencia, trabajos y persistencia de revisiones.
- `backend/app/main.py`: se combina automáticamente. Hay que conservar el
  lifespan/trabajos de feature y la composición única de imágenes de main,
  además de ambos routers de Laboratorio y el router común de IA.
- `frontend/src/features/inicio/pages/InicioPage.jsx`: se combina automáticamente;
  falta verificar destinos por rol y acceso separado a Ecografía y Rayos X.
- main introduce `backend/app/imagenes/application/ports.py`, mientras IA tiene
  `application/ports/vision.py`: revisar resolución de imports y contrato de
  ambos puertos; una combinación textual no demuestra inferencia funcional.
- main reorganiza entidades, modelos, schemas, servicios y rutas de Laboratorio
  en paquetes. Conservar esa estructura y revisar imports desde módulos vecinos.
- main incorpora solicitud/publicación de Ecografía y consulta médica de
  resultados de Laboratorio. No deben eliminarse al agregar el análisis IA.
- main también cambia dictado, extracción clínica y transportador. No se
  descartaron esos cambios, pero aún no están integrados en esta rama.
- main cambia Docker Compose y settings. Deben conservarse pgvector y los
  límites de privacidad/localidad, sin agregar proveedores externos.
- No hay diferencias entre HEAD y origin/main en `backend/requirements.txt`,
  `backend/requirements-radiologia.txt`, `backend/requirements-rag.txt`,
  `frontend/package.json` ni `frontend/package-lock.json`.

## Seguridad y archivos no publicables

- Existe un `.env` raíz **ya versionado**, con `DATABASE_URL`, `JWT_SECRET_KEY`
  y `DEBUG` no vacíos, incorporado históricamente en `594c335`. No se imprimieron
  valores ni se copiaron a este informe. No hay secretos nuevos preparados.
- Antes de publicar: dejar ese archivo local fuera del índice, agregar su regla
  de exclusión y revisar/rotar cualquier credencial real expuesta. Desversionar
  no borra el historial. No se autorizó ni se hizo reescritura de historial.
- `backend/.env` y `frontend/.env` están ignorados en el checkout original.
- Ya están versionados dos `.pyc` en `transportador/app/__pycache__/` y artefactos
  en `.playwright-mcp/`; main añade `backend/_ellos_cola.tmp`. Revisarlos antes
  de publicación; no se eliminaron automáticamente.
- La búsqueda por nombres de archivos no encontró pesos `.pt`, `.pth`,
  `.safetensors`, `.onnx`, claves `.pem`/`.key`, audio `.wav` ni DICOM `.dcm`
  versionados en HEAD. Esto NO sustituye una auditoría de contenido clínico
  y secretos de todo el diff combinado.

## Verificaciones realmente ejecutadas

En el worktree de diagnóstico, ANTES de cualquier integración de código:

- Python **3.12.10**, intérprete del entorno ya existente del checkout original.
- Variables ficticias de proceso, DB apuntando a puerto local no disponible;
  no se cargaron credenciales del checkout original para estas verificaciones.
- `import app.main`: correcto en **feature sin integrar**.
- `python -m pip check`: sin requisitos incompatibles en ese entorno.
- `pytest -q app/imagenes/tests/test_fusion_hallazgos.py tests/test_historial_migraciones_unificado.py`:
  **15 passed in 0.49s**, exclusivamente en feature sin integrar.
- Simulación del grafo combinado y reproducción repetida del salto de Ecografía:
  bloqueo confirmado sin conexión a BD ni ejecución de migraciones.
- Node **24.14.0**, npm **11.9.0** disponibles en el entorno original.
- Docker responde con motor Linux. No se crearon bases ni contenedores.

No se ejecutaron suite completa, tests/lint/build de frontend, flujos clínicos,
inferencias TorchXRayVision, embeddings, recuperación RAG real, prueba offline,
pgvector en BD ni migraciones contra datos. No se presentan resultados antiguos
de la documentación como verificaciones de esta integración.

## Estado de módulos

| Módulo | Estado |
| --- | --- |
| Laboratorio | Cambios de main identificados y conservados en origin/main; todavía no integrados ni probados en conjunto. |
| Ecografía | Cambios de main identificados; bloqueo de actualización de catálogo reproducido. Flujo clínico no verificado. |
| Rayos X e IA | Rama original y respaldo intactos; comprobación limitada de import/fusión/historial pasa. Inferencia, RAG y operación integrada no verificados. |
| Migraciones | Divergencia histórica confirmada; una cabeza aparente no garantiza que Ecografía se ejecute. No se modificó ningún archivo histórico ni esquema. |

## Continuación y eventual publicación

1. Resolver y aprobar la estrategia de historial antes descrita.
2. Implementar en esta rama aislada, sin modificar main, y añadir regresiones
   para las rutas de actualización de cada historial aplicado.
3. Ejecutar el merge pendiente con origin/main, resolver los seis conflictos
   semánticamente y revisar también las combinaciones automáticas.
4. Validar backend, frontend, permisos, módulos, inferencia/RAG reales y bases
   aisladas. Revisar secretos y artefactos, diff y marcadores antes del commit.
5. Solo con verificaciones satisfactorias, publicar la rama de integración
   mediante `git push -u origin integracion/main-rayos-x-20261109` y abrir PR
   hacia main para revisión. **Ese comando no se ejecutó y no debe ejecutarse
   todavía.** No hay un comando seguro para integrar el estado actual en main.
6. Si origin/main avanzó durante la revisión, volver a actualizar referencias,
   integrar sus cambios y repetir las verificaciones afectadas. Sin force push.

Único cambio preparado en este trabajo: este informe de diagnóstico. El commit
local que lo contiene no es un commit de integración ni permite declarar el
merge exitoso.
