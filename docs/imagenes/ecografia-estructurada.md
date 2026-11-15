# Ecografía: solicitudes, observaciones por órgano y láminas

## Recorrido

El rol `imagenes` abre `/ecografia` y puede crear una **Nueva solicitud**: buscar y
seleccionar un paciente existente, indicar el médico solicitante y elegir uno o
varios tipos de ecografía. El médico conserva también la solicitud desde la ficha
de Consultas. La clave idempotente evita duplicados al reintentar el envío.

Al abrir un estudio, el formulario muestra la plantilla de su código de catálogo:

| Código | Campos |
| --- | --- |
| ECO_ABDOMINAL | Hígado, vías biliares, vesícula biliar, páncreas, bazo, riñones derecho e izquierdo |
| ECO_OBSTETRICA | Embrión o feto, líquido amniótico, placenta, cordón umbilical |
| ECO_GINECOLOGICA | Útero, ovarios, trompas de Falopio, fondo de saco de Douglas |
| ECO_RENAL | Riñones derecho e izquierdo, vías urinarias, vejiga |
| ECO_PARTES_BLANDAS | Piel, tejido subcutáneo, músculos, tendones, ganglios de la zona |
| ECO_TIROIDEA | Lóbulos derecho e izquierdo, istmo, ganglios cervicales |
| ECO_MAMARIA | Glándulas mamarias y regiones axilares, derecha e izquierda |
| ECO_DOPPLER | Arterias y venas de la zona estudiada |

Cada campo es texto libre para registrar observaciones y mediciones con unidades.
No hay valores normales, conclusiones ni diagnósticos prellenados. Si una estructura
no se evalúa o no se visualiza, se indica expresamente; no equivale a un hallazgo
normal. Doppler y partes blandas requieren identificar la zona al publicar.

Se guardan fecha del estudio, establecimiento, zona, observaciones y conclusión
manual. El borrador puede quedar incompleto. Para publicar se deben completar
fecha, conclusión y cada campo. El botón exige guardar antes de publicar, y la
publicación se confirma en un diálogo. El backend valida las mismas condiciones.

## Varios adjuntos

El selector acepta varios archivos y acumula nuevas selecciones, sin reemplazar
las anteriores. Antes de guardar se pueden quitar archivos nuevos o retirar
adjuntos de la versión siguiente. Guardar texto conserva los adjuntos actuales.
Solo se aceptan IDs de adjuntos de la versión actual del mismo estudio; no se
pueden incorporar archivos de otro paciente mediante un ID.

El máximo continúa siendo configurable mediante `IMAGENES_MAX_ARCHIVOS` (10 por
defecto), incluyendo adjuntos conservados y nuevos. No significa almacenamiento
ilimitado. Los formatos y límites por archivo mantienen la configuración del
módulo. PNG/JPEG/WebP y otros formatos de imagen admitidos se muestran en láminas;
PDF/DICOM se conservan como adjuntos, sin convertirlos ni incrustarlos como imagen.

## Informe e impresión

La vista previa organiza lo escrito por órgano, seguido de conclusión, identificación
del paciente, fecha, establecimiento y médico solicitante. La edad se calcula a la
fecha del estudio. No se copia información del paciente de las fotos de referencia.
El espacio de firma y sello no sustituye una firma electrónica del profesional.

**Imprimir o guardar PDF** usa el diálogo de impresión del navegador. Oculta el editor
y los controles, conserva la marca de borrador si corresponde y coloca las imágenes
en láminas de dos columnas a partir de una página nueva. Antes de imprimir deben
haberse guardado los cambios y cargado las imágenes. La paginación final depende del
navegador, tamaño de papel y contenido; no es un PDF generado en el servidor.

Los informes publicados siguen siendo de solo lectura y están disponibles en el
historial del paciente, con el texto compuesto y los adjuntos. Los informes antiguos
de texto libre conservan su contenido y su pantalla. No se convierten automáticamente
en plantillas ni se sobrescriben.

## Persistencia y comprobación del 14/11/2026

La migración incremental `20261114_0017`, hija de `20261111_0016`, agrega únicamente
`informe_imagen.datos_ecografia` JSONB nullable y una restricción de objeto. Cada
versión guarda la plantilla y sus valores; el texto legible se compone en el dominio.
El ORM utiliza `none_as_null=True` para que los informes históricos sin plantilla
conserven SQL NULL. No se reescriben migraciones anteriores ni el bootstrap.

Se respaldó la base local y se restauró en un PostgreSQL aislado con tmpfs y puerto
loopback 55441. La copia se migró antes de actualizar la instalación local; las filas
anteriores de 60 tablas se compararon por huellas sin mostrar contenido clínico.
Sin pérdidas ni diferencias en las filas anteriores. Respaldo fuera de Git:
`backend/.storage/backups/sarco-pre-eco-20261114.dump`.

Suite backend después de actualizar: 401 aprobadas, 33 omitidas. Incluye un flujo
HTTP/PostgreSQL con login real y rollback: crear solicitud desde Imágenes, dos
adjuntos, borrador oculto al médico, bloqueo de publicación incompleta, añadir una
tercera imagen, conservar/retirar adjuntos, rechazar IDs ajenos, publicar y consultar
el informe con sus imágenes como médico. Solo datos ficticios.

Frontend: 89 pruebas, lint y build correctos. Las omisiones backend corresponden a
matriz histórica optativa, inferencia offline/real y condiciones de plataforma;
no se afirma haber repetido IA real. Los modelos de Rayos X no intervienen en este
flujo manual de Ecografía.
