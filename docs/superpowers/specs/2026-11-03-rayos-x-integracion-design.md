# Integración experimental de Rayos X en SarcoSistema

Estado: diseño aprobado en conversación. La solicitud actual denomina esta integración «Fase 4»; sustituye la numeración del maestro para esta entrega. Antes de implementarla, cerrar la prueba y revisión de RAG local pendiente. Sin entrenamiento ni descarga de LLM nuevo.

## Situación comprobada

Backend modular FastAPI, auth JWT/RBAC existente, PostgreSQL16, tablas `estudio_solicitado`, `informe_imagen`, `archivo_imagen`; servicio IMG. No existe router clínico de imágenes ni pantalla React funcional de Rayos X. Frontend tiene Laboratorio y Consultas, sin feature imagenes. La base local tiene cero informes y cero archivos de imagen. No asumir estudios o archivos disponibles ni inventar un flujo ya existente.

## Flujo de esta entrega

Agregar `/imagenes` dentro de la aplicación existente, sin aplicación separada. Usar layout, tipografía, colores, tablas, paneles y botones de Laboratorio mediante estilos/componentes compartidos o parametrizables; no reutilizar rótulos de Laboratorio en Rayos X ni alterar su flujo.

El médico autenticado ve estudios IMG autorizados y selecciona un estudio. Panel de detalle: paciente ficticio/de investigación autorizado, radiografía PNG/JPEG local y descripción del informe publicado en modo lectura. Mostrar estado vacío si no hay estudios o archivos, y errores distintos por permisos, preparación, RAM y timeout. Sin descarga de fuentes/CDN ni URL de imagen externa indispensable.

El operador confirma tórax frontal y vista PA/AP/frontal no especificada. Solicita análisis con clave idempotente y snapshot de versión/hash del archivo e informe. El backend inicia trabajo controlado fuera del event loop y devuelve id/estado; frontend consulta estado y permite volver sin duplicar trabajo. Una inferencia por entorno, visión y embeddings secuenciales, trabajadores efímeros y timeout. Reinicio del proceso marca trabajos interrumpidos, no deja «procesando» indefinidamente. Datos clínicos originales nunca se escriben por inferencia.

Salida distingue cuatro bloques: scores visuales experimentales (no porcentajes clínicos), texto informado y extracción conservadora con evidencia/negaciones/incertidumbre, coincidencias o discrepancias para revisión, y citas del corpus local. No convertir un score en hallazgo confirmado ni comparar con un umbral clínico inventado. Si se usa un criterio técnico para destacar discrepancias, documentarlo como heurística configurable, no diagnóstico. Frases ambiguas quedan indeterminadas; la cita original acompaña toda extracción. No resolver contradicciones automáticamente.

RAG usa solo corpus local verificado, pgvector y modelo preparado. Si falla o falta evidencia, mostrar «información insuficiente» o componente no disponible, preservando los resultados visuales válidos y sin inventar una explicación. Sin LLM obligatorio: la generación estructurada es el modo de esta entrega.

El médico puede registrar revisión «aceptada como propuesta», «corregida» o «rechazada», con observaciones y motivo obligatorio al corregir/rechazar. Guardado explícito, actor y fecha del servidor; concurrencia optimista evita pisar una revisión ajena. Revisión aceptada no equivale a diagnóstico validado ni publica/rectifica `informe_imagen`. Historial de revisiones se conserva; no borrado físico.

## Autorización y archivos

Reutilizar `usuario_actual`, `requiere_rol('medico')` y usuario/trabajador/médico existente. Decisión propuesta: acceso a los estudios solicitados por el propio médico, denegando por defecto solicitudes sin vínculo autorizado; probar también acceso directo por ids. No abrir todos los estudios por tener un JWT. El backend valida permiso antes de leer imagen, informe, fuente asociada, análisis o revisión. No exponer paths locales al cliente.

Leer archivos únicamente desde una raíz local configurada; rechazar traversal, enlaces que salgan de la raíz, URLs externas, formatos no admitidos, bytes/hash/tamaño incompatibles y archivos retirados. Servir bytes con autorización; no usar rutas clínicas públicas ni confiar en MIME enviado por cliente. No añadir soporte DICOM ni subir imágenes a proveedores externos.

## Persistencia incremental

Agregar tablas separadas para análisis y revisiones por Alembic, con FK a estudio/informe/archivo/usuario, estado de trabajo, snapshots y hashes, versiones del modelo/corpus, resultado JSON experimental, errores seguros y timestamps. Índice/constraint idempotente por solicitante y clave; reintento con payload distinto se rechaza. Historial de revisión append-only y versión de concurrencia. No modificar diagnósticos ni tablas de otros módulos. Auditoría usa mecanismos existentes donde apliquen, comprobando actores/transacciones.

## Demostración y pruebas

Como no hay informes/archivos existentes, preparar de forma explícita y no destructiva un estudio ficticio accesible al médico de prueba, usando radiografía autorizada de investigación. Cualquier texto ficticio adjunto debe indicar «simulación de integración, no informe auténtico de esa imagen»; no emparejarlo como registro real. No renovar claves ni tocar cuentas ajenas. Las pruebas usarán rollback o recursos propios acotados.

Pruebas: permisos y acceso por id, archivo inválido, modelo/corpus ausente, cola/concurrencia/doble envío, timeout/reinicio, negaciones/incertidumbre, citas exactas y abstención, revisión explícita y concurrente, inmutabilidad de informe/diagnóstico, flujo browser completo contra backend y modelos reales preparados. Ejecutar flujo sin salida Internet, medición de RAM/latencia, regresiones backend y frontend; reportar mocks/omisiones y no confundir pruebas de UI con inferencia real. Detenerse al verificar la entrega y documentar limitaciones.

## Exclusiones

No crear un módulo operativo de gestión radiológica completo, carga masiva/datasets, DICOM, PACS, diagnósticos autónomos, publicación automática, entrenamiento, LLM nuevo ni modificar módulos ajenos salvo extracción mínima de componentes compartidos y wiring. No commits/push ni eliminación de datos/volúmenes actuales.
