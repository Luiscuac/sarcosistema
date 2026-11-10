# Rayos X: integración experimental local

Implementación en la rama `feat/rayos-x`, dentro de SarcoSistema. Esta entrega corresponde al alcance llamado «Fase 4» en la última solicitud: integra visión, recuperación documental y revisión médica, **sin exigir un LLM**. No es un sistema diagnóstico validado ni una implementación clínica operativa.

## Qué permite

- Entrar desde Inicio → **Rayos X**, con rol `medico`, o abrir `/imagenes`.
- Seleccionar estudios IMG publicados solicitados por el propio médico. Las peticiones por ID comprueban la misma autorización.
- Visualizar la radiografía PNG/JPEG local con autenticación y el informe publicado en modo lectura.
- Confirmar tórax frontal/proyección y solicitar análisis. La respuesta inicial es HTTP 202; la pantalla consulta el estado del trabajo persistido.
- Ver scores experimentales de consolidación, derrame pleural y cardiomegalia; términos descritos, negados, inciertos o ambiguos del informe; comparaciones para revisión; citas del corpus local o información insuficiente.
- Registrar explícitamente aceptación **como propuesta experimental**, corrección o rechazo. Corregir/rechazar exige motivo; corregir exige texto. Se conservan actor, fecha y versiones de revisión.

**Ninguna de estas operaciones publica, rectifica ni convierte una propuesta en diagnóstico definitivo.** La revisión de IA se guarda separada de `informe_imagen`. La interfaz reutiliza sidebar, topbar y estilos de Laboratorio sin cambiar sus opciones predeterminadas.

## Preparación y arranque

1. Comprobar que `backend/.env` apunta a PostgreSQL local correcto y que sus credenciales funcionan. No reemplazar un `.env` existente ni cambiar contraseñas para arreglar una prueba.
2. Con Docker/PostgreSQL iniciado, aplicar migraciones desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

La cabecera actual de esta rama es `20261109_0012`, unión de los historiales de Laboratorio e IA. En la rama IA, `20261103_0008` agrega el corpus pgvector y `20261103_0009` agrega `imagen_analisis_ia` e `imagen_revision_ia`. Si una instalación contiene objetos de ambas ramas pero registra solo una, consultar el ensayo de reconciliación antes de migrar; no repetir DDL ni usar `stamp` sin verificación. **No volver a ejecutar `database/schema.sql` sobre una base existente ni borrar volúmenes.**

3. Preparar previamente las dependencias, pesos y documentos opcionales según [visión local](fase-2-vision-local.md) y [RAG local](fase-3-rag-local.md). Si ya están preparados, conservarlos. Indexar el corpus en la base que usará el backend:

```powershell
.\.venv\Scripts\python.exe -m scripts.consultar_rag_torax --indexar
```

4. Habilitar explícitamente estas variables locales (están documentadas sin secretos en `.env.example`):

```dotenv
RADIOLOGY_AI_ENABLED=true
RADIOLOGY_STORAGE_DIR=.storage/radiologia
RADIOLOGY_VISION_MIN_FREE_MIB=4096
RADIOLOGY_SCORE_THRESHOLD=0.5
```

La asistencia viene deshabilitada. El listado/informe manual no necesita cargar Torch. Los paths relativos se resuelven respecto de `backend/`; no se admiten URLs externas para leer las imágenes.

5. Desde `backend/`, iniciar el backend; en otra terminal, desde `frontend/`, iniciar Vite:

```powershell
# backend/
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

```powershell
# frontend/
npm run dev
```

Usar `http://localhost:5173`, como en CORS. Tras cambiar de rama, reiniciar el backend; no confiar en un proceso antiguo del watcher. Identificar procesos antes de detenerlos.

## Demostración ficticia optativa

La base de partida no tenía informes ni archivos radiológicos. Se agregó un preparador **no destructivo**, no una carga automática al iniciar:

```powershell
# backend/, solo PostgreSQL local migrado y usuario médico ficticio ya preparado
.\.venv\Scripts\python.exe -m scripts.preparar_estudio_imagen_demo --preparar-demo --usuario medico_demo
```

Si todavía no existe esa cuenta ficticia, `scripts.preparar_medico_demo` la prepara y conserva la contraseña en un archivo local externo al repositorio. No renovará ni reemplazará cuentas ajenas. No asumir una contraseña o ID sembrado.

El preparador radiológico crea `RX-DEMO-IA-001` y un paciente reservado nuevos; aborta ante colisiones. Copia la muestra autorizada `NIH-RX-001.png` preparada en Fase 2, verificando su SHA-256. Conserva el original y su atribución NIH en los manifiestos.

**El informe demo dice expresamente «SIMULACIÓN DE INTEGRACIÓN» y no es el informe auténtico de esa imagen.** Solo sirve para probar integración, negaciones e incertidumbre; no demuestra precisión clínica ni constituye un caso real emparejado. `.storage/`, `.models/`, `.datasets/` y `.radiologia-resultados/` están excluidos de Git.

## Procesamiento, recursos y fallos

El ejecutor usa una cola persistida, liderazgo PostgreSQL y el lock local compartido por los modelos. Visión y embeddings se ejecutan **secuencialmente**, en trabajadores CPU efímeros. No se descargan pesos/documentos durante una solicitud.

- Visión conserva su timeout de 120 s y control de RAM; embeddings tiene timeout de 180 s y mínimo de 2 GiB libres.
- El mínimo visual general sigue en 4 GiB. Solo para la demostración acotada de muestras de 512×512 se utilizó explícitamente 2048 MiB, tras las mediciones previas de ~400 MiB RSS visual. No extrapolar ese perfil a otras imágenes ni eliminar los bloqueos.
- Las transacciones de solicitud y finalización son cortas; no se mantiene la sesión clínica de la petición abierta durante inferencia.
- El líder vigila su conexión. Claim/recuperación se ejecutan en la conexión propietaria del lock; la finalización comprueba PID e inicio de sesión del líder. Al perder liderazgo no reclama más trabajos ni publica resultados como propietario anterior. El trabajador ya iniciado puede tardar hasta su timeout en liberar recursos.
- Tras reinicio, trabajos que estaban procesando se marcan interrumpidos. Un reintento con la misma clave/datos devuelve el mismo análisis; cambiar el contenido reutilizando clave se rechaza.
- Se verifican informe/archivo al solicitar y antes/después de inferir. La pantalla oculta resultados que no corresponden al snapshot actual y no conserva una imagen retirada como si fuera vigente.
- Si falla el componente documental, incluso su base de datos, se conserva la visión válida y se muestra RAG no disponible, sin inventar fuentes.
- La revisión guarda la versión contra la que comenzó el borrador. Un refetch no la sustituye silenciosamente: se exige reconciliar una revisión nueva y no se pierde el borrador sin confirmación.

La extracción del informe es una heurística acotada a tres términos, no NLP clínico validado. Trata incertidumbre y alcance de negación conservadoramente, pero puede omitir contextos. El umbral 0,5 solo destaca scores normalizados; **no es un umbral clínico**, ni representa 50 % de probabilidad. Ningún score bajo descarta enfermedad.

## API implementada

Todas las rutas reutilizan JWT, usuario actual, rol médico y autorización del estudio:

- `GET /imagenes/estudios`, `GET /imagenes/estudios/{id}`.
- `GET /imagenes/estudios/{id}/archivos/{archivo_id}`: bytes locales verificados, sin URL pública del archivo.
- `POST /imagenes/estudios/{id}/analisis`: confirmación de tórax frontal, proyección y clave idempotente.
- `GET /imagenes/analisis/{id}` y `GET /imagenes/analisis/{id}/fuentes`.
- `POST /imagenes/analisis/{id}/revision`: versión esperada, decisión, motivo y corrección opcional.

La API no permite subida de imágenes, edición/publicación de informes ni administración radiológica general en esta entrega. Las fuentes se presentan como citas locales; la URL bibliográfica es referencia, no una búsqueda web durante la consulta.

## Verificación realizada antes de la pausa

Estos resultados corresponden a las ejecuciones previas al reinicio, **no a una nueva ejecución el 09/11/2026**:

- Backend: **280 passed, 11 skipped**, 64,93 s. PostgreSQL temporal propio en `localhost:55432`, bootstrap únicamente por ser una base nueva y nueve migraciones aplicadas. Las omisiones incluyen pruebas optativas de IA/offline/POSIX y symlink en Windows por privilegios.
- Frontend: **27 passed**; ESLint y build correctos. `pip check` sin dependencias rotas; importación de `app.main` correcta y sin cargar Torch.
- `frontend/tests/imagenes.browser.js`: inicio de sesión real, acceso al estudio, imagen real, modelos reales, fuentes y revisión persistida tras recargar; cero recursos externos solicitados por la interfaz.
- `frontend/tests/imagenes-conflictos.browser.js`: revisión concurrente por API real y borrador retenido con su versión original. **El retiro de archivo se simuló solo en la respuesta de detalle**; se comprobó que desaparecen la imagen y el resultado incompatible. No presentarlo como modificación real de un archivo clínico.

Para repetir las pruebas browser con el runner Playwright del entorno, crear fuera de Git `backend/.radiologia-resultados/integracion-browser-config.json` con `frontend`, `api`, `usuario` y `key_path` al archivo local de contraseña de la cuenta ficticia. Los scripts leen la clave sin imprimirla ni imprimir JWT. Usar exclusivamente datos de prueba.

### Flujo API real sin salida a Internet

Se construyó online `Dockerfile.imagenes-integracion-test` reutilizando los artefactos CPU de Fases 2/3. Luego se ejecutó el harness `scripts.verificar_imagenes_offline` con los **routers, autenticación, repositorios y ejecutor reales**, no dobles de inferencia, en una red Docker creada con `--internal` junto a un PostgreSQL temporal propio. La base fue una copia exclusivamente de los datos ficticios preparados para esta prueba.

Runtime: raíz readonly, montajes de pesos/corpus/imagen readonly, cuota 3 GiB, dos CPU y tmpfs. No se montó el checkpoint pickle original de visión, solo manifest y safetensors. La prueba intentó una conexión real del SO a `1.1.1.1:443` y exigió su fallo. No se deshabilitó la conectividad de Windows.

El comando terminó correctamente y comprobó:

- Imagen autorizada local y token validado contra el usuario real de la base de prueba.
- Visión CPU y embeddings/RAG reales; **cuatro citas locales**.
- Reintento idempotente del POST con el mismo ID de análisis.
- Revisión persistida y conflicto de versión HTTP 409.
- Informe publicado idéntico antes y después; sin diagnósticos automáticos.

Scores observados en esa muestra, **experimentales, no probabilidades**: Consolidation 0,312433; Effusion 0,394274; Cardiomegaly 0,621515. Visión: 0,995 s de pase, 27,714 s completos y 456.507.392 bytes (~435 MiB) de RSS máxima observada del hijo. La cuota de 3 GiB no es una medición del pico total de RAG.

La prueba browser comprobó la aplicación completa con backend real en Windows; el harness offline comprobó la API del módulo y modelos reales aislados. **No se ejecutó un navegador dentro del contenedor aislado ni se apagaron físicamente los adaptadores del host.** Ambos alcances se distinguen para no exagerar la evidencia.

Para repetir, preparar primero una base temporal con los datos ficticios, migraciones y corpus indexado; no usar una copia con pacientes reales. Construir la imagen, poner base y harness en una red `--internal`, montar artefactos readonly y establecer `DATABASE_URL` a esa base, un `JWT_SECRET_KEY` exclusivamente ficticio, `RADIOLOGY_AI_ENABLED=true` y el perfil visual de prueba. Ejecutar:

```powershell
# backend/; construcción durante preparación online
docker build -f Dockerfile.imagenes-integracion-test -t sarcosistema-imagenes-integracion:test .
# El CMD ejecuta python -m scripts.verificar_imagenes_offline.
# No ejecutar el harness fuera de la red aislada: debe fallar si alcanza Internet.
```

### Estado del entorno al retomar el cierre

El 09/11/2026 Docker Desktop no expone su motor Linux: la inspección de los contenedores/red devuelve «pipe … dockerDesktopLinuxEngine … no encontrado». No se reconstruyeron contenedores ni se repitieron modelos para el cierre documental, y **no se afirma que el entorno esté levantado actualmente**.

En la verificación anterior `localhost:5432` rechazó las credenciales del `.env`; no se cambió su contraseña ni su configuración. Las pruebas usaron únicamente la base temporal propia en 55432, sin modificar datos/volúmenes de la instalación del usuario. Antes de usar la pantalla en su instalación, iniciar Docker/PostgreSQL y comprobar su `DATABASE_URL`, migraciones, corpus y archivos locales. Las bases tmpfs de prueba son volátiles tras reinicios; no asumir que conservan el demo.

## Revisión y límites

La revisión independiente identificó cinco hallazgos importantes: alcance de negación/incertidumbre, pérdida de visión por fallo de BD del RAG, pérdida de liderazgo, mezcla de snapshots en UI y versión de borrador reemplazada por refetch. Se reprodujeron con pruebas y se corrigieron. También se corrigió la imagen obsoleta al retirar su fuente. Las pruebas reales de navegador detectaron etiquetas de formulario inestables y se corrigieron con asociaciones explícitas.

Pendiente menor de cobertura: comprobar el symlink de archivos en Linux, porque Windows lo omitió por privilegios; no se atribuye ese caso al harness que no lo ejecutó. Los límites documentados del RAG pequeño y sus pruebas adicionales de lifecycle siguen en [Fase 3](fase-3-rag-local.md).

Esta entrega no incluye LLM, DICOM/PACS, subida de archivos, carga masiva, publicación automática ni precisión clínica validada. No se hicieron commits ni push de este cierre. Se detiene aquí, sin avanzar a otra fase.
