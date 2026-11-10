# Reconciliación de migraciones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Ejecución directa de la preparación/prueba en copia autorizada por el usuario; no aplicar nada sobre la base original.

**Goal:** Reunir el historial Laboratorio de main y el historial IA de feat/rayos-x, verificando reconciliación sin pérdida de datos en una copia.
**Architecture:** Conservar las revisiones existentes sin reescribirlas; incorporar las cuatro revisiones exactas de main y una revisión merge sin DDL. La base actual registra solo main0011 aunque contiene objetos IA: validar los objetos IA contra una referencia recién migrada antes de corregir exclusivamente el registro Alembic de la copia.
**Tech Stack:** Alembic, PostgreSQL16/pgvector, Docker local, Python3.12, pytest.
**Spec:** Autorización en conversación: preparar reconciliación y probar primero en copia, sin modificar la original.

## Global Constraints
- Sin checkout, merge Git, commits, push, downgrade ni cambios a revisiones existentes.
- No ejecutar stamp/upgrade sobre la base original; no tocar sus datos ni contraseñas.
- Dump local privado fuera de Git; no imprimir datos clínicos, claves ni hashes de contraseñas.
- Nuevos recursos propios con nombres únicos, puertos locales automáticos y sin montar el volumen original.
- No Fase5 ni cambios a extracción, RAG o módulos clínicos.

## Review Focus
- Copiar main sin cambiar contenido ni colisionar con archivos existentes.
- Tablas IA parciales o incompatibles: detener reconciliación antes de stamp.
- Dos historiales divergentes desde 0007: preservar ambas cabezas y converger por merge sin DDL.
- Datos/identidades/secuencias: comparar antes/después de reconciliar, excluyendo solo alembic_version.
- Destino original: comprobar separadamente URL/nombre de copia antes de cualquier comando de migración.

### Task1: Respaldo y referencia aislados
- [ ] Respaldar base actual con pg_dump custom en directorio temporal privado único; restaurar en contenedor propio.
- [ ] Crear una segunda base nueva de referencia con schema.sql solo por estar vacía y aplicar únicamente la rama IA hasta 0009.
- [ ] Comparar contrato completo de las cuatro tablas IA (columnas/tipos/defaults/constraints/índices/triggers), función de inmutabilidad y extensión vector. Ante diferencia, detenerse.

### Task2: Historial reunido
**Files:** agregar sin cambios las cuatro migraciones main0008–0011; crear `backend/alembic/versions/20261109_0012_unificar_laboratorio_ia.py`; pruebas `backend/tests/test_historial_migraciones_unificado.py`.
- [ ] RED: ScriptDirectory tiene una cabeza 0012 con ancestros main0011, IA0009 y común0007; hashes de archivos main idénticos al commit de origen.
- [ ] Incorporar archivos exactos y merge con down_revision=('20261103_0011','20261103_0009'), upgrade sin DDL y downgrade bloqueado.
- [ ] GREEN: pruebas de grafo y contenido; referencia IA sigue migrando hasta su propia cabeza sin ejecutar rama Laboratorio.

### Task3: Ensayo de reconciliación y regresiones
- [ ] Solo tras igualdad de contrato: registrar las dos cabezas ya materializadas en LA COPIA, preservando main0011, y aplicar el merge0012.
- [ ] Comparar huellas de filas, esquema IA y secuencias antes/después (excepto alembic_version); comprobar una cabeza final y ausencia de cambios en original.
- [ ] Crear tercera base nueva y comprobar upgrade desde bootstrap hasta head unificado sin stamp; ambas rutas deben funcionar.
- [ ] Ejecutar pruebas antes bloqueadas y suite predeterminada contra copia; prueba RAG real DB separada para distinguir el fallo conocido de aislamiento de event loops.
- [ ] Revisión independiente acotada a reconciliación, documentar resultados y detenerse. Pedir autorización adicional antes de aplicar en original.

## Progreso y decisiones
Plan autorizado por el sí a preparar/probar una copia. No se necesita otra aprobación para ese ensayo; la aplicación en original queda explícitamente fuera de alcance.

### Evidencia del ensayo (09/11/2026)
- Task1 completada: respaldo custom privado restaurado en PostgreSQL temporal separado; 58 tablas con filas idénticas al respaldo. Referencia vacía inicializada y migrada hasta IA0009; contrato de cuatro tablas, extensión y función comparado sin diferencias. Se corrigió solo la serialización del diagnóstico privado: convertir tipos internos PostgreSQL `char` a texto.
- Task2 completada: seis pruebas RED (faltaban archivos/cabeza) y luego seis GREEN. Cuatro archivos idénticos byte a byte al commit `68625b83eeed5e1eb9f044e6c360f0c4d4ce5f13`; merge0012 sin DDL y downgrade bloqueado.
- Task3 ensayo completado: exclusivamente en `recon_copia2_2369abf061`, registro de ambas cabezas materializadas y upgrade0012. Comparación inmediata confirmó mismas filas, las 51 secuencias y contrato IA intactos.
- Ruta limpia independiente: `recon_nueva_2369abf061`, bootstrap solo sobre base vacía y `upgrade head`, sin stamp; revisión0012 y contrato IA correcto.
- Suite predeterminada contra copia: **286 passed, 11 skipped in 40.72s**. RAG con `RUN_RAG_DB_TESTS=1` en proceso separado: **3 passed in 0.42s**. No se afirma que desapareció el fallo conocido de event loops al combinar RAG opcional y Consultas en un mismo proceso; no se modificó ese código.
- Verificación posterior de original: mismas filas y revisión `20261103_0011` que antes del ensayo. No recibió stamp ni upgrade. Sus secuencias no tenían captura previa: no se afirma comparación antes/después de ellas en original.
- Ruling: continuar en la rama de trabajo autorizada y añadir solo archivos de reconciliación, sin trasladar los cambios locales de integración a un worktree nuevo; aislamiento de datos mediante contenedor/base separados. Coste si fuera incorrecto: los archivos nuevos comparten workspace, pero ninguna operación Git descarta o cambia trabajo existente.
- No commits ni push. Respaldo, credenciales temporales y logs permanecen fuera del repositorio en el directorio privado de OpenCode; no contienen instrucciones para aplicar ciegamente stamp en otra instalación.
- Revisión independiente completada: identificó dependencia de las pruebas en un commit histórico que un checkout superficial de CI no garantiza. Corregido con SHA256 esperados del origen y normalización exclusiva CRLF/LF; cuatro fallos RED al simular historial ausente, luego suite final **286 passed, 11 skipped in 40.18s**. Sin otros hallazgos.
- Pendiente: autorización separada antes de cualquier aplicación en original. **No ejecutar `alembic upgrade head` directamente en la original:** intentaría crear objetos IA ya existentes. Primero requiere la reconciliación verificada de su tracking. No comenzar Fase5.

### Aplicación en original autorizada
El usuario autorizó explícitamente la aplicación después del ensayo mediante «sí». Esta autorización amplía exclusivamente la restricción de no migrar la original; siguen vigentes la conservación de datos, ausencia de downgrade, commits y push, y la exclusión de Fase5.
- [x] Comprobar destino local, revisión0011 y contrato IA; capturar filas/secuencias y crear respaldo custom nuevo.
- [x] Registrar ambas cabezas materializadas y aplicar merge0012, como en el ensayo.
- [x] Comparar inmediatamente filas, secuencias y contrato; ejecutar regresiones y registrar resultados.

Aplicación autorizada completada: base local original en `20261109_0012 (head) (mergepoint)`. Comparación inmediata antes/después: filas de 58 tablas, 51 secuencias y contrato IA sin cambios. Respaldo custom nuevo y evidencia privada guardados en `aplicacion_original_326ec849` dentro del directorio temporal de reconciliación. Suite sobre original: **286 passed, 11 skipped in 40.17s**; RAG opcional en proceso separado: **3 passed in 0.33s**. La limitación conocida del event loop al combinar la prueba RAG opcional con Consultas no se modificó ni se declara resuelta. Sin commits, push ni Fase5; los errores de extracción señalados en auditoría siguen fuera de este cambio.
