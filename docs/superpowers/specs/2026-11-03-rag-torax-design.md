# Fase 3: RAG local de tórax

Diseño aprobado en conversación: recuperación local en PostgreSQL/pgvector, embeddings preparados antes de consultar, documentos médicos verificables locales, referencias exactas y abstención. Sin frontend, publicación clínica ni cambios a registros clínicos. Solo datos ficticios en pruebas. No commits ni push.

Decisiones de implementación propuestas por el agente: multilingual-e5-small (384 dimensiones), sujeto a licencia y medición CPU/RAM; corpus pequeño de artículos médicos abiertos con licencia explícita que permita almacenamiento, preferentemente PMC Open Access. Guardar original, URL, licencia, fecha y SHA-256; referencias por sección y offsets del texto extraído, sin inventar páginas. Preparación online explícita; runtime local_files_only, sin código remoto ni descargas.

Usar tablas nuevas aisladas mediante Alembic incremental: documento y fragmento con vector, metadatos de procedencia, versión de extracción y modelo. No reutilizar tablas clínicas ni reejecutar schema.sql. Búsqueda parametrizada, orden determinista y límites de entrada. Ingesta idempotente y rechazo de modelos/corpus incompatibles o alterados.

Salida estructurada por defecto: evidencia textual recuperada, referencias verificadas y advertencias experimentales. La similitud no es certeza clínica. Abstenerse para consultas fuera de alcance, ausencia de evidencia o evidencia insuficiente; validar negaciones y no convertir recuperación en diagnóstico. No atribuir al corpus frases que no contiene. Ollama solo loopback, optativo y condicionado por recursos; si se habilita, validar citas y regresar a salida estructurada ante error, timeout o respuesta no sustentada. No es necesario descargar otro LLM para cumplir esta fase.

Prueba offline en red Docker interna sin salida externa: PostgreSQL debe ser accesible al proceso RAG, por lo que network none solo no sirve para el flujo completo. Artefactos montados readonly, comprobación real de conexión externa fallida, búsqueda pgvector real, citas exactas, generación estructurada y abstención. No modificar adaptadores/firewall del host ni borrar volúmenes existentes. Detenerse tras verificar y documentar límites.
