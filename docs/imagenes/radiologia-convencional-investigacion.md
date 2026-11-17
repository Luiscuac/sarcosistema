# Radiología convencional: investigación para el módulo de Rayos X

> 16/11/2026. Base clínica y técnica del rediseño del módulo. El catálogo detallado (estudios, proyecciones, lateralidad, plantillas) está en [radiologia-convencional-catalogo.md](radiologia-convencional-catalogo.md), generado desde `backend/app/imagenes/domain/catalogo_radiologia.py`.
>
> Prototipo universitario con datos ficticios. Los contenidos clínicos son orientativos y deben ser validados por el servicio de radiología del centro.

## 1. Cómo funciona un servicio de radiología convencional

Flujo habitual en un centro de diagnóstico general:

1. **Solicitud**: el médico tratante pide un estudio indicando región, lateralidad cuando aplica, indicación clínica y, a veces, proyecciones o protocolo.
2. **Recepción / admisión**: se identifica al paciente, se registra la orden (uno o varios estudios) y queda en la lista de trabajo.
3. **Adquisición**: el técnico radiólogo posiciona al paciente, adquiere las proyecciones y registra lo realizado (que puede diferir de lo solicitado: paciente que no puede ponerse de pie, proyección repetida, proyección no obtenible).
4. **Control de calidad**: el técnico revisa colimación, posicionamiento, movimiento y exposición; repite si es necesario y lo registra.
5. **Interpretación**: el médico (radiólogo o médico autorizado) revisa las imágenes junto a la indicación y estudios previos, y redacta el informe.
6. **Validación / firma**: el informe pasa de borrador a final. Una vez final, cualquier cambio se hace como **adenda o rectificación** con trazabilidad, nunca sobrescribiendo.
7. **Entrega / comunicación**: el informe final se pone a disposición del solicitante; los hallazgos urgentes o inesperados requieren comunicación directa documentada (ACR, *Communication of Diagnostic Imaging Findings*).

## 2. Estudio, protocolo y proyección

Para no duplicar el catálogo:

| Concepto | Ejemplo | Dónde vive |
|---|---|---|
| **Estudio** (lo que se solicita e informa) | Radiografía de rodilla | Catálogo (`tipo_estudio`) |
| **Lateralidad** (dato de la solicitud) | Derecha | Detalle del estudio solicitado |
| **Protocolo** (proyecciones habituales para una indicación) | AP y lateral; con carga | Catálogo, como preselección |
| **Proyección** (una exposición) | AP en bipedestación | Solicitada y realizada, por separado |

Por eso "tórax PA", "tórax AP" y "tórax PA y lateral" son protocolos del estudio *Radiografía de tórax*, y "cadera derecha/izquierda/bilateral" es la lateralidad del estudio *Radiografía de cadera*. Las proyecciones solicitadas **no implican** que se hayan realizado: el técnico registra las realizadas.

## 3. Datos que registra el técnico (adquisición)

Fuentes: ACR–AAPM–SIIM–SPR *Practice Parameter for Digital Radiography*; IEC 62494-1 y DICOM PS3.3 *Exposure Index Macro*.

| Dato | Tipo | Obligatorio | Nota |
|---|---|---|---|
| Proyecciones realizadas | Lista del catálogo del estudio | Sí, para cerrar la adquisición | Puede diferir de lo solicitado |
| Lateralidad realizada | Derecha / izquierda / bilateral | Si el estudio la requiere | Debe coincidir con el marcador radiopaco |
| Posición del paciente | Bipedestación, sedestación, decúbito supino/prono/lateral | No | |
| Fecha y hora de adquisición | Fecha/hora | Sí | |
| Operador responsable | Usuario del sistema | Automático | |
| Número de imágenes | Entero | Automático (archivos subidos) | |
| Calidad / limitaciones técnicas | Selector + texto | No | Rotación, movimiento, inspiración, colimación |
| Repeticiones y motivo | Entero + texto | No | |
| kVp | Número (40–150) | No | Configurable por equipo |
| mAs | Número | No | |
| Tiempo de exposición | ms | No | |
| Índice de exposición (EI) / índice de desviación (DI) | Número | No | IEC 62494-1; DICOM (0018,1411)/(0018,1413) |
| Producto dosis-área (DAP) | µGy·m² / dGy·cm² | No | Solo si el equipo lo informa |
| Equipo / sala | Texto | No | |

Los parámetros técnicos **no** forman parte de los campos diagnósticos del informe; solo se resumen en "Técnica" si el médico lo decide.

## 4. Qué evalúa el médico y estructura del informe

El ACR (*Practice Parameter for Communication of Diagnostic Imaging Findings*) recomienda un informe con:

1. **Datos demográficos**: centro, paciente con dos identificadores, fecha del examen, médico solicitante.
2. **Indicación clínica**.
3. **Técnica / procedimiento**: estudio, proyecciones realizadas, limitaciones.
4. **Comparación** con estudios previos (o constancia de que no hay).
5. **Hallazgos**: descripción organizada por estructuras anatómicas.
6. **Impresión / conclusión**: síntesis y diagnóstico diferencial cuando corresponda. Es la parte más leída: debe ser concisa.
7. **Recomendaciones**, cuando correspondan.
8. **Profesional responsable, fecha de validación y firma**.

Las plantillas estructuradas (RSNA RadReport, p. ej. *Chest Xray*) organizan los hallazgos por apartados anatómicos con texto libre. Este proyecto sigue ese criterio:

- Apartados **guía** por región (catálogo), todos **opcionales**.
- **Frases sugeridas** que solo se insertan si el médico las elige: nunca se completan solas, ni siquiera los hallazgos negativos.
- **Mediciones** opcionales con unidad y rango (índice cardiotorácico, ángulo de Cobb, calibre de asa, edad ósea).
- **Conclusión obligatoria** para validar.
- El texto final se compone desde los apartados y el médico puede revisarlo antes de validar.

### Tipos de datos

| Tipo | Ejemplos | Implementación |
|---|---|---|
| Estructurado | Lateralidad, proyecciones, protocolo, método de edad ósea | Selectores |
| Medición | ICT, ángulo de Cobb, calibre de asa | Número + unidad + rango válido |
| Descriptivo | Hallazgos por apartado, conclusión, recomendaciones | Texto libre |

## 5. Imágenes y vínculo con el estudio

- Formatos: **DICOM** (estándar del equipo; el proyecto ya decodifica DICOM y genera una vista PNG), JPG y PNG (digitalizadas o exportadas), y PDF solo como **informe externo** o documento adjunto.
- Cada archivo se vincula al estudio y, opcionalmente, a la **proyección realizada**.
- El binario se guarda fuera de la base de datos con hash SHA-256; la base solo guarda metadatos. Nunca se guarda en Base64 en tablas transaccionales.
- El acceso es solo por endpoints autenticados con control de rol y pertenencia; no hay rutas públicas.
- Retirar o reemplazar un archivo exige motivo y conserva el original (borrado lógico), solo antes de la validación del informe.
- Los metadatos DICOM contienen identificadores del paciente (PatientName, PatientID): se usan para verificar la correspondencia y no se exponen innecesariamente.

## 6. Estados del estudio

Referencia del encargo adaptada al flujo existente de `estudio_solicitado`:

```
solicitado → pendiente_realizacion → en_adquisicion → imagenes_obtenidas → pendiente_informe → borrador → validado → entregado
                     ↘ no_realizado (con motivo)        ↘ repeticion (registrada en la adquisición)
validado → rectificado (nueva versión con motivo; la anterior se conserva)
```

## 7. Fuentes

- American College of Radiology. [ACR Practice Parameter for Communication of Diagnostic Imaging Findings](https://gravitas.acr.org/PPTS/GetDocumentView?docId=74).
- ACR–SPR–STR. [Practice Parameter for the Performance of Chest Radiography](https://www.acr.org/-/media/ACR/Files/Practice-Parameters/ChestRad.pdf) y [Portable Chest Radiography](https://www.acr.org/-/media/ACR/Files/Practice-Parameters/Port-Chest-Rad.pdf).
- ACR–ASSR–SPR–SSR. [Practice Parameter for the Performance of Spine Radiography](https://gravitas.acr.org/PPTS/GetDocumentView?docId=152).
- ACR–SPR–SSR. [Practice Parameter for the Performance of Radiography of the Extremities](https://gravitas.acr.org/PPTS/DownloadPreviewDocument?DocId=12).
- ACR. [Practice Parameter for the Performance of Radiography for Scoliosis in Children](https://www.acr.org/-/media/ACR/Files/Practice-Parameters/scoliosis.pdf).
- RSNA. [RadReport reporting templates](https://www.rsna.org/practice-tools/data-tools-and-standards/radreport-reporting-templates).
- RadiologyInfo (ACR/RSNA). [X-ray (Radiography)](https://www.radiologyinfo.org/en/x-ray).
- NEMA. [DICOM PS3.3 — Exposure Index Macro](https://dicom.nema.org/medical/dicom/2019e/output/chtml/part03/sect_10.19.html); IEC 62494-1:2008.
- Tsalafoutas et al. [Exposure index in digital radiography and its dependence on acquisition parameters](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12802571/).
- The Royal College of Radiologists. [Adapted anatomical image criteria for PA chest radiography](https://www.rcr.ac.uk/career-development/audit-quality-improvement/auditlive-radiology-templates/adapted-anatomical-image-criteria-for-pa-chest-radiography/).
- Textos de posicionamiento: Bontrager & Lampignano, *Textbook of Radiographic Positioning and Related Anatomy*; Merrill's *Atlas of Radiographic Positioning and Procedures*.
