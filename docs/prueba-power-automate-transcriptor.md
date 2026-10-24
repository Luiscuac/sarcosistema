# Prueba de Power Automate Desktop con SarcoSistema

Esta prueba usa únicamente tres registros ficticios servidos por `GET /ia/transcriptor/registros`. No lee ni escribe las tablas clínicas.

## Preparar

1. Inicia backend y frontend como en el README del proyecto e inicia sesión en SarcoSistema.
2. Abre `http://localhost:5173/transcriptor` en Edge o Chrome. Deben aparecer `PA-TEST-001`, `PA-TEST-002` y `PA-TEST-003`.
3. En Power Automate Desktop crea un flujo y agrega **Iniciar nuevo Microsoft Edge** con esa dirección. Usa la grabadora web para capturar la pantalla de transcripción.
4. Crea una aplicación local de prueba con campos de texto Código, Nombre, Fecha, Examen, Resultado y Unidad (por ejemplo, un formulario de prueba en otra pestaña o una aplicación demo).

## Flujo sugerido

1. Con **Hacer clic en elemento de página web**, selecciona el registro `PA-TEST-001`.
2. Usa **Obtener detalles del elemento de página web** para capturar el texto de los seis campos de la vista previa.
3. Abre la aplicación de destino de prueba e introduce cada variable en su campo con **Rellenar campo de texto en página web** o las acciones de escritorio equivalentes.
4. Detente antes de guardar y revisa que el formulario de destino muestre `Paciente de prueba Uno`, `Hemoglobina`, `13.8` y `g/dL`.

La interfaz también ofrece **Copiar campos**, que copia una fila tabulada para probar pegado en formularios; PAD puede leer cada campo directamente si la grabadora web reconoce los controles.

## Selectores estables

- Fila del registro: `data-testid="registro-demo-001"` (cambia el sufijo para los otros registros).
- Campos: `campo-codigo`, `campo-nombre`, `campo-fecha`, `campo-examen`, `campo-resultado`, `campo-unidad`.
- Endpoint autenticado: `GET http://localhost:8000/ia/transcriptor/registros`.

Para probar sin sesión, el endpoint debe responder `401`; con una sesión válida responde JSON. El contenido es deliberadamente fijo y ficticio para que una prueba de interfaz no copie datos clínicos.
