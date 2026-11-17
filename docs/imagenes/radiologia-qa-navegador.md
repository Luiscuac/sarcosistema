# Rayos X: prueba funcional en navegador (17/11/2026)

Entorno local: PostgreSQL en Docker migrado a `20261116_0019`, uvicorn y Vite. Cuentas de prueba ficticias (técnico, radiólogo, médico).

## Recorrido verificado

| Paso | Rol | Resultado |
|---|---|---|
| Bandeja con indicadores y filtros | técnico | Correcto |
| Nueva solicitud: paciente, estudio (rodilla), lateralidad, protocolo, médico, confirmación | técnico | Correcto; el registro aparece en "Pendientes de realización" |
| Registro técnico, subida de imagen con proyección, completar adquisición | técnico | Correcto tras corregir que "Completar" ignoraba lo escrito sin guardar |
| Informe en solo lectura | técnico | Correcto (no puede redactar) |
| Visor, informe por plantilla, borrador, validación con pendientes y confirmación | radiólogo | Correcto; la validación guarda el borrador antes |
| Informe impreso | radiólogo | Correcto |
| Informe validado en la ficha del paciente | médico | Correcto |

> Nota 17/11/2026: después de esta prueba se eliminó el rol `radiologo`; el informe lo redacta y valida `rayos_x`.

## Correcciones hechas

- Tildes: "Indicación clínica", "Tórax" (filtro), posiciones del paciente, "versión", textos de confirmación.
- La lateralidad ya no se preselecciona en "Derecha": el usuario debe elegirla.
- "Completar adquisición" guarda primero el formulario.
- Botones sin estilo (Guardar registro, Guardar borrador, Seguir editando, Volver).
- Tamaño de archivo legible (B/KB/MB) y singular en "1 archivo adjunto".
- El asistente de IA solo se ofrece en estudios de tórax.
- Sin numeración "2." en la solicitud del médico.
- Error de carga de imagen visible (antes quedaba en "Cargando…").
- Permisos: la ruta heredada ya no deja al radiólogo subir imágenes de Rayos X (403, con prueba).

## Pendiente (no bloqueante)

- Dos diálogos modales apilados en "Nueva solicitud" (accesibilidad).
- Pestañas de imágenes del informe sin `tabIndex`/`aria-controls`.
- Códigos internos como respaldo en algunos textos (decisión de revisión IA, `actor {id}`).
- No se probó la solicitud completa desde la ficha del médico ni la subida de DICOM en navegador.

## Nueva solicitud en pantalla completa (17/11/2026)

- Ya no es una ventana: `/rayos-x/gestion/solicitudes/nueva`, con paciente y catálogo a la izquierda, y estudios elegidos, datos del pedido y botones (fijos) a la derecha.
- Se quitó el **protocolo** del formulario (duplicaba las proyecciones). Las proyecciones solicitadas son opcionales y están en "Más opciones"; el backend ya no las exige.
- Al registrar, redirige a la solicitud creada.
