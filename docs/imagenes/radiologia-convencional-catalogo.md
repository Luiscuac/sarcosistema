# Catálogo de radiología convencional

> Generado desde `backend/app/imagenes/domain/catalogo_radiologia.py` (versión 1). No editar a mano: modificar el catálogo y volver a ejecutar `scripts/generar_doc_catalogo_rx.py`.

Orientativo: cada centro debe validar con su servicio de radiología qué estudios y protocolos habilita según su equipamiento.

## Campos generales de todo informe

| Campo | Uso |
|---|---|
| Técnica | Proyecciones realizadas y condiciones del estudio. Se propone desde la adquisición registrada y es editable. |
| Indicación clínica | Motivo del examen según la solicitud. Editable. |
| Comparación | Estudios previos comparados con su fecha, o indique que no hay estudios previos disponibles. |
| Limitaciones técnicas | Rotación, inspiración insuficiente, movimiento, superposición, proyecciones no obtenidas. |
| Conclusión / impresión diagnóstica | Obligatoria para validar. Redáctela usted; el sistema no propone diagnósticos. |
| Recomendaciones | Solo cuando correspondan (correlación clínica, estudio complementario, control). |

Solo la **conclusión** es obligatoria para validar. Los apartados de cada plantilla son guías de lectura opcionales.

## Matriz de estudios

| Código | Estudio | Categoría | Lateralidad | Proyecciones aplicables | Protocolos | Plantilla | Fuente |
|---|---|---|---|---|---|---|---|
| `RX_TORAX` | Radiografía de tórax | Tórax | No aplica | Posteroanterior (PA), Lateral, Anteroposterior (AP), AP en decúbito supino, AP lordótica (vértices), Decúbito lateral con rayo horizontal | PA; AP (paciente que no puede ponerse de pie / portátil); PA y lateral | Tórax | ACR-SPR-STR Practice Parameter for the Performance of Chest Radiography; RSNA RadReport "Chest Xray". |
| `RX_COSTILLAS` | Radiografía de parrilla costal | Tórax | Derecha / izquierda / bilateral | Anteroposterior (AP), Posteroanterior (PA), Oblicua | AP/PA y oblicua del lado afectado | Parrilla costal y esternón | Posicionamiento radiográfico estándar (Bontrager; Merrill). |
| `RX_ESTERNON` | Radiografía de esternón | Tórax | No aplica | Oblicua anterior derecha (OAD), Lateral | Oblicua anterior derecha y lateral | Parrilla costal y esternón | Posicionamiento radiográfico estándar (Bontrager; Merrill). |
| `RX_ABDOMEN` | Radiografía de abdomen simple | Abdomen | No aplica | AP en decúbito supino, AP en bipedestación, Decúbito lateral con rayo horizontal, Posteroanterior (PA) | Decúbito supino; De pie; Decúbito lateral con rayo horizontal; Serie de abdomen agudo (supino, de pie y PA de tórax) | Abdomen | ACR Appropriateness Criteria (dolor abdominal, obstrucción); Posicionamiento radiográfico estándar (Bontrager; Merrill). |
| `RX_COL_CERVICAL` | Radiografía de columna cervical | Columna vertebral | No aplica | Anteroposterior (AP), Lateral, AP transoral (C1-C2, boca abierta), Oblicua derecha, Oblicua izquierda, Lateral en flexión, Lateral en extensión, Lateral de nadador (cervicotorácica) | AP y lateral; AP, lateral y transoral; Laterales dinámicas (flexión y extensión) | Columna vertebral | ACR-ASSR-SPR-SSR Practice Parameter for the Performance of Spine Radiography. |
| `RX_COL_DORSAL` | Radiografía de columna dorsal | Columna vertebral | No aplica | Anteroposterior (AP), Lateral, Lateral de nadador (cervicotorácica) | AP y lateral | Columna vertebral | ACR-ASSR-SPR-SSR Practice Parameter for the Performance of Spine Radiography. |
| `RX_COL_LUMBAR` | Radiografía de columna lumbar | Columna vertebral | No aplica | Anteroposterior (AP), Lateral, Lateral focalizada L5-S1, Oblicua derecha, Oblicua izquierda, Lateral en flexión, Lateral en extensión | AP y lateral; AP, lateral y L5-S1; Oblicuas (pars interarticularis); Laterales dinámicas | Columna vertebral | ACR-ASSR-SPR-SSR Practice Parameter for the Performance of Spine Radiography. |
| `RX_COL_LUMBOSACRA` | Radiografía de columna lumbosacra | Columna vertebral | No aplica | Anteroposterior (AP), Lateral, Lateral focalizada L5-S1, Oblicua derecha, Oblicua izquierda | AP, lateral y L5-S1 | Columna vertebral | ACR-ASSR-SPR-SSR Practice Parameter for the Performance of Spine Radiography. |
| `RX_SACRO_COCCIX` | Radiografía de sacro y cóccix | Columna vertebral | No aplica | AP axial (angulada), Lateral | AP axial y lateral | Columna vertebral | ACR-ASSR-SPR-SSR Practice Parameter for the Performance of Spine Radiography. |
| `RX_COL_TOTAL` | Telerradiografía de columna (escoliosis) | Columna vertebral | No aplica | Posteroanterior (PA), Anteroposterior (AP), Lateral | PA (o AP) y lateral en bipedestación | Columna vertebral | ACR-SPR-SSR Practice Parameter for the Performance of Radiography for Scoliosis in Children. |
| `RX_PELVIS` | Radiografía de pelvis | Pelvis y cadera | No aplica | Anteroposterior (AP) | AP de pelvis | Pelvis y cadera | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_CADERA` | Radiografía de cadera | Pelvis y cadera | Derecha / izquierda / bilateral | Anteroposterior (AP), Lateral en rana (Lauenstein), Axial lateral de cadera (rayo horizontal) | AP y lateral en rana; AP y axial lateral (sospecha de fractura: no usar rana) | Pelvis y cadera | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_CLAVICULA` | Radiografía de clavícula | Extremidades superiores | Derecha / izquierda | Anteroposterior (AP), AP axial (angulada) | AP y AP axial | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_ESCAPULA` | Radiografía de escápula | Extremidades superiores | Derecha / izquierda | Anteroposterior (AP), Lateral en Y escapular | AP y lateral en Y | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_HOMBRO` | Radiografía de hombro | Extremidades superiores | Derecha / izquierda | AP en rotación interna, AP en rotación externa, AP verdadera de glenoides (Grashey), Axilar, Lateral en Y escapular | AP en rotación interna y externa; Grashey y lateral en Y (o axilar) | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_HUMERO` | Radiografía de húmero | Extremidades superiores | Derecha / izquierda | Anteroposterior (AP), Lateral | AP y lateral | Hueso largo | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_CODO` | Radiografía de codo | Extremidades superiores | Derecha / izquierda / bilateral | Anteroposterior (AP), Lateral, Oblicua interna, Oblicua externa | AP y lateral; AP, lateral y oblicuas | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_ANTEBRAZO` | Radiografía de antebrazo | Extremidades superiores | Derecha / izquierda / bilateral | Anteroposterior (AP), Lateral | AP y lateral | Hueso largo | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_MUNECA` | Radiografía de muñeca | Extremidades superiores | Derecha / izquierda / bilateral | Posteroanterior (PA), Lateral, Oblicua, PA con desviación cubital (escafoides) | PA, oblicua y lateral; Serie de escafoides | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_MANO` | Radiografía de mano | Extremidades superiores | Derecha / izquierda / bilateral | Posteroanterior (PA), Oblicua, Lateral | PA y oblicua; PA, oblicua y lateral | Mano / pie | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_DEDOS_MANO` | Radiografía de dedos de la mano | Extremidades superiores | Derecha / izquierda | Posteroanterior (PA), Oblicua, Lateral | PA, oblicua y lateral | Mano / pie | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_EDAD_OSEA` | Radiografía para edad ósea | Extremidades superiores | No aplica | Posteroanterior (PA) | PA de mano y muñeca izquierda | Edad ósea | Greulich y Pyle; Tanner-Whitehouse. |
| `RX_FEMUR` | Radiografía de fémur | Extremidades inferiores | Derecha / izquierda | Anteroposterior (AP), Lateral | AP y lateral | Hueso largo | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_RODILLA` | Radiografía de rodilla | Extremidades inferiores | Derecha / izquierda / bilateral | Anteroposterior (AP), Lateral, Oblicua interna, Oblicua externa, Túnel intercondíleo, Axial de rótula (Merchant / sol naciente), AP en bipedestación | AP y lateral; AP en bipedestación y lateral (artrosis); AP, lateral, túnel y axial de rótula | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_ROTULA` | Radiografía de rótula | Extremidades inferiores | Derecha / izquierda / bilateral | Posteroanterior (PA), Lateral, Axial de rótula (Merchant / sol naciente) | Lateral y axial | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_TIBIA_PERONE` | Radiografía de tibia y peroné | Extremidades inferiores | Derecha / izquierda | Anteroposterior (AP), Lateral | AP y lateral | Hueso largo | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_TOBILLO` | Radiografía de tobillo | Extremidades inferiores | Derecha / izquierda / bilateral | Anteroposterior (AP), AP de mortaja, Lateral, Con carga (bipedestación) | AP, mortaja y lateral | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_PIE` | Radiografía de pie | Extremidades inferiores | Derecha / izquierda / bilateral | Dorsoplantar (AP de pie), Oblicua, Lateral, Con carga (bipedestación) | Dorsoplantar, oblicua y lateral; Dorsoplantar y lateral con carga | Mano / pie | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_DEDOS_PIE` | Radiografía de dedos del pie | Extremidades inferiores | Derecha / izquierda | Dorsoplantar (AP de pie), Oblicua, Lateral | Dorsoplantar, oblicua y lateral | Mano / pie | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_CALCANEO` | Radiografía de calcáneo | Extremidades inferiores | Derecha / izquierda / bilateral | Axial de calcáneo (plantodorsal), Lateral | Axial y lateral | Articulación periférica | ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill). |
| `RX_CRANEO` | Radiografía de cráneo | Cráneo y estructuras faciales | No aplica | PA de Caldwell, AP axial de Towne, Lateral | PA (Caldwell), Towne y lateral | Cráneo | ACR Appropriateness Criteria (traumatismo craneal: TC de elección); Posicionamiento radiográfico estándar (Bontrager; Merrill). |
| `RX_HUESOS_NASALES` | Radiografía de huesos nasales | Cráneo y estructuras faciales | No aplica | Lateral, Occipitomentoniana (Waters) | Laterales y Waters | Huesos nasales | Posicionamiento radiográfico estándar (Bontrager; Merrill). |
| `RX_SENOS_PARANASALES` | Radiografía de senos paranasales | Cráneo y estructuras faciales | No aplica | PA de Caldwell, Occipitomentoniana (Waters), Lateral, Submentovértice | Caldwell, Waters y lateral (en bipedestación) | Senos paranasales | ACR Appropriateness Criteria (sinusitis); Posicionamiento radiográfico estándar (Bontrager; Merrill). |
| `RX_HUESOS_FACIALES` | Radiografía de huesos faciales | Cráneo y estructuras faciales | No aplica | Occipitomentoniana (Waters), PA de Caldwell, Lateral, Submentovértice | Waters, Caldwell y lateral | Huesos faciales | Posicionamiento radiográfico estándar (Bontrager; Merrill). |
| `RX_CAVUM` | Radiografía de cavum (partes blandas de cuello) | Cuello y partes blandas | No aplica | Lateral, Anteroposterior (AP) | Lateral de cuello / cavum | Partes blandas de cuello / cavum | Posicionamiento radiográfico estándar (Bontrager; Merrill). |

## Notas y datos adicionales por estudio

- **Radiografía de tórax** (`RX_TORAX`): Evaluación de pulmones, corazón, mediastino, pleura y estructuras óseas del tórax. La proyección AP magnifica la silueta cardíaca; indíquelo al valorar su tamaño.
- **Radiografía de parrilla costal** (`RX_COSTILLAS`): Evaluación de arcos costales, habitualmente por traumatismo. Dato requerido en la solicitud: Arcos superiores o inferiores al diafragma, si se conoce. Suele acompañarse de una PA de tórax para descartar neumotórax.
- **Radiografía de esternón** (`RX_ESTERNON`): Evaluación del esternón, habitualmente por traumatismo.
- **Radiografía de abdomen simple** (`RX_ABDOMEN`): Evaluación del patrón de gas intestinal, calcificaciones y cuerpos extraños. Dato requerido en la solicitud: Protocolo indicado por el médico solicitante. Los niveles hidroaéreos y el aire libre solo se valoran con rayo horizontal.
- **Radiografía de columna cervical** (`RX_COL_CERVICAL`): Evaluación de vértebras C1-C7 y su alineación. La lateral debe incluir C7-T1; si no, considerar proyección de nadador.
- **Radiografía de columna dorsal** (`RX_COL_DORSAL`): Evaluación de vértebras T1-T12.
- **Radiografía de columna lumbar** (`RX_COL_LUMBAR`): Evaluación de vértebras L1-L5.
- **Radiografía de columna lumbosacra** (`RX_COL_LUMBOSACRA`): Evaluación de columna lumbar y unión lumbosacra.
- **Radiografía de sacro y cóccix** (`RX_SACRO_COCCIX`): Evaluación del sacro y cóccix, habitualmente por traumatismo.
- **Telerradiografía de columna (escoliosis)** (`RX_COL_TOTAL`): Evaluación de escoliosis en bipedestación; permite medir ángulo de Cobb. Estudio ampliado: requiere chasis o detector largo; deshabilitar si el equipo no lo permite.
- **Radiografía de pelvis** (`RX_PELVIS`): Evaluación de pelvis ósea, sacroilíacas y ambas caderas.
- **Radiografía de cadera** (`RX_CADERA`): Evaluación de la articulación coxofemoral. Ante sospecha de fractura de cadera no realizar la proyección en rana.
- **Radiografía de hombro** (`RX_HOMBRO`):  En traumatismo no rotar el brazo.
- **Radiografía de dedos de la mano** (`RX_DEDOS_MANO`):  Dato requerido en la solicitud: Dedo(s): pulgar, índice, medio, anular o meñique.
- **Radiografía para edad ósea** (`RX_EDAD_OSEA`): Estimación de la maduración esquelética en pediatría. Por convención se usa la mano izquierda.
- **Radiografía de dedos del pie** (`RX_DEDOS_PIE`):  Dato requerido en la solicitud: Dedo(s) del pie.
- **Radiografía de cráneo** (`RX_CRANEO`): Uso limitado; en traumatismo craneal la TC es el estudio de elección.
- **Radiografía de senos paranasales** (`RX_SENOS_PARANASALES`): Uso limitado; la TC es de elección en sinusitis complicada.
- **Radiografía de cavum (partes blandas de cuello)** (`RX_CAVUM`): Evaluación de tejido adenoideo en pediatría y de vía aérea.

## Plantillas de evaluación

### Tórax (`torax`)

Estudios: Radiografía de tórax.

| Apartado | Tipo | Guía |
|---|---|---|
| Campos pulmonares | Descriptivo | Opacidades, consolidación, nódulos, patrón intersticial, hiperinsuflación. |
| Silueta cardiomediastínica | Descriptivo | Tamaño y contornos cardíacos; valorar con cautela en proyección AP. |
| Índice cardiotorácico | Medición, opcional | Opcional. Solo interpretable en PA de buena calidad. |
| Mediastino e hilios | Descriptivo | Ensanchamiento, desviación traqueal, adenopatías hiliares. |
| Pleuras y senos costofrénicos | Descriptivo | Derrame, engrosamiento, neumotórax. |
| Diafragma y espacio subdiafragmático | Descriptivo | Elevación, aire libre subdiafragmático. |
| Estructuras óseas y partes blandas | Descriptivo | Fracturas costales, lesiones líticas o blásticas, enfisema subcutáneo. |
| Dispositivos y catéteres | Descriptivo | Tubos, catéteres, marcapasos: tipo y posición. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Parrilla costal y esternón (`parrilla_costal`)

Estudios: Radiografía de parrilla costal, Radiografía de esternón.

| Apartado | Tipo | Guía |
|---|---|---|
| Arcos costales | Descriptivo | Trazos de fractura, desplazamiento, callos, lesiones focales. |
| Esternón | Descriptivo | Integridad cortical, alineación de segmentos, articulaciones esternoclaviculares. |
| Pleura y pulmón visibles | Descriptivo | Neumotórax, derrame o contusión asociados. |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Abdomen (`abdomen`)

Estudios: Radiografía de abdomen simple.

| Apartado | Tipo | Guía |
|---|---|---|
| Distribución del gas intestinal | Descriptivo | Patrón inespecífico, ausencia de gas distal, gas en recto. |
| Dilatación de asas | Descriptivo | Intestino delgado o colon; calibre y distribución. |
| Calibre máximo de asa | Medición (cm), opcional | Opcional; indique el segmento medido en el texto. |
| Niveles hidroaéreos | Descriptivo | Solo evaluables en bipedestación o decúbito con rayo horizontal. Indique si la técnica no lo permite. |
| Aire libre / neumoperitoneo | Descriptivo | Requiere técnica con rayo horizontal o tórax de pie. |
| Calcificaciones | Descriptivo | Litiasis renal o biliar, calcificaciones vasculares o pancreáticas. |
| Cuerpos extraños | Descriptivo | Radiopacos: tipo y localización. |
| Siluetas de órganos sólidos y psoas | Descriptivo | Hepatomegalia, esplenomegalia, borramiento del psoas. |
| Estructuras óseas visibles | Descriptivo | Columna lumbar y pelvis visibles. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Columna vertebral (`columna`)

Estudios: Radiografía de columna cervical, Radiografía de columna dorsal, Radiografía de columna lumbar, Radiografía de columna lumbosacra, Radiografía de sacro y cóccix, Telerradiografía de columna (escoliosis).

| Apartado | Tipo | Guía |
|---|---|---|
| Alineación vertebral | Descriptivo | Listesis, escoliosis, alineación de líneas espinales. |
| Curvatura | Descriptivo | Lordosis/cifosis fisiológica, rectificación o acentuación. |
| Ángulo de Cobb | Medición (°), opcional | Opcional; indique los niveles medidos en el texto. |
| Altura y morfología de cuerpos vertebrales | Descriptivo | Acuñamientos, aplastamientos, lesiones focales. |
| Espacios intervertebrales | Descriptivo | Disminución de altura, vacío discal. |
| Cambios degenerativos | Descriptivo | Osteofitos, esclerosis de platillos, artrosis facetaria. |
| Pedículos y elementos posteriores | Descriptivo | Integridad de pedículos, espondilólisis (en oblicuas). |
| Lesiones óseas | Descriptivo | Líticas, blásticas o fracturas. |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Material de osteosíntesis / dispositivos | Descriptivo | Posición e integridad del material; aflojamiento o rotura. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Pelvis y cadera (`pelvis_cadera`)

Estudios: Radiografía de pelvis, Radiografía de cadera.

| Apartado | Tipo | Guía |
|---|---|---|
| Alineación y relaciones articulares | Descriptivo | Congruencia coxofemoral, sínfisis y sacroilíacas. |
| Integridad ósea | Descriptivo | Fracturas de cuello femoral, trocantéricas, ramas pubianas, acetábulo. |
| Espacio articular coxofemoral | Descriptivo | Pinzamiento, simetría. |
| Cambios degenerativos | Descriptivo | Osteofitos, esclerosis subcondral, quistes. |
| Cabeza femoral | Descriptivo | Esfericidad, densidad (necrosis avascular), epífisis en pediatría. |
| Lesiones óseas focales | Descriptivo |  |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Material de osteosíntesis / dispositivos | Descriptivo | Posición e integridad del material; aflojamiento o rotura. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Articulación periférica (`articulacion`)

Estudios: Radiografía de clavícula, Radiografía de escápula, Radiografía de hombro, Radiografía de codo, Radiografía de muñeca, Radiografía de rodilla, Radiografía de rótula, Radiografía de tobillo, Radiografía de calcáneo.

| Apartado | Tipo | Guía |
|---|---|---|
| Alineación ósea y relaciones articulares | Descriptivo | Luxación, subluxación, congruencia. |
| Integridad de estructuras óseas | Descriptivo | Trazos de fractura, desplazamiento, angulación, conminución. |
| Espacios articulares | Descriptivo | Pinzamiento, simetría compartimental. |
| Cambios degenerativos | Descriptivo | Osteofitos, esclerosis subcondral, geodas. |
| Derrame articular | Descriptivo | Signos indirectos de derrame (p. ej. almohadillas grasas). |
| Lesiones óseas focales | Descriptivo |  |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Material de osteosíntesis / dispositivos | Descriptivo | Posición e integridad del material; aflojamiento o rotura. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Hueso largo (`hueso_largo`)

Estudios: Radiografía de húmero, Radiografía de antebrazo, Radiografía de fémur, Radiografía de tibia y peroné.

| Apartado | Tipo | Guía |
|---|---|---|
| Alineación | Descriptivo | Angulación, rotación, acortamiento. |
| Cortical y medular | Descriptivo | Trazos de fractura, reacción perióstica, lesiones focales. |
| Articulaciones proximal y distal | Descriptivo | Incluidas en el estudio: relaciones articulares. |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Material de osteosíntesis / dispositivos | Descriptivo | Posición e integridad del material; aflojamiento o rotura. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Mano / pie (`mano_pie`)

Estudios: Radiografía de mano, Radiografía de dedos de la mano, Radiografía de pie, Radiografía de dedos del pie.

| Apartado | Tipo | Guía |
|---|---|---|
| Alineación y relaciones articulares | Descriptivo | Luxaciones, deformidades (hallux valgus, desviación cubital). |
| Integridad ósea | Descriptivo | Fracturas de falanges, metacarpianos/metatarsianos, huesos del carpo/tarso. |
| Espacios articulares | Descriptivo | Pinzamiento, erosiones. |
| Cambios degenerativos o inflamatorios | Descriptivo | Osteofitos, erosiones, osteopenia periarticular. |
| Densidad ósea | Descriptivo |  |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Material de osteosíntesis / dispositivos | Descriptivo | Posición e integridad del material; aflojamiento o rotura. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Cráneo (`craneo`)

Estudios: Radiografía de cráneo.

| Apartado | Tipo | Guía |
|---|---|---|
| Bóveda craneal | Descriptivo | Trazos de fractura, lesiones líticas o blásticas, suturas. |
| Base de cráneo y silla turca | Descriptivo |  |
| Calcificaciones intracraneales visibles | Descriptivo |  |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Senos paranasales (`senos_paranasales`)

Estudios: Radiografía de senos paranasales.

| Apartado | Tipo | Guía |
|---|---|---|
| Senos maxilares | Descriptivo | Neumatización, engrosamiento mucoso, niveles hidroaéreos (solo en bipedestación), opacificación. |
| Senos frontales | Descriptivo |  |
| Celdillas etmoidales | Descriptivo |  |
| Seno esfenoidal | Descriptivo | Mejor valorado en lateral. |
| Tabique nasal y cornetes | Descriptivo | Desviación, hipertrofia. |
| Paredes óseas | Descriptivo | Integridad, erosión. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Huesos nasales (`huesos_nasales`)

Estudios: Radiografía de huesos nasales.

| Apartado | Tipo | Guía |
|---|---|---|
| Integridad de huesos nasales | Descriptivo | Trazos de fractura, desplazamiento, hundimiento. |
| Espina nasal anterior y tabique | Descriptivo |  |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Huesos faciales (`huesos_faciales`)

Estudios: Radiografía de huesos faciales.

| Apartado | Tipo | Guía |
|---|---|---|
| Órbitas | Descriptivo | Rebordes orbitarios, suelo de órbita. |
| Arcos y huesos cigomáticos | Descriptivo |  |
| Maxilar y mandíbula | Descriptivo | Trazos de fractura, cóndilos. |
| Senos maxilares | Descriptivo | Hemoseno, nivel hidroaéreo en contexto traumático. |
| Partes blandas | Descriptivo | Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Edad ósea (`edad_osea`)

Estudios: Radiografía para edad ósea.

| Apartado | Tipo | Guía |
|---|---|---|
| Edad cronológica | Medición (años), opcional |  |
| Edad ósea estimada | Medición (años), opcional |  |
| Método | Selector: Greulich y Pyle / Tanner-Whitehouse (TW3) / Otro |  |
| Núcleos de osificación y fisis | Descriptivo | Descripción de núcleos y estado de cartílagos de crecimiento. |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

### Partes blandas de cuello / cavum (`cuello_partes_blandas`)

Estudios: Radiografía de cavum (partes blandas de cuello).

| Apartado | Tipo | Guía |
|---|---|---|
| Vía aérea | Descriptivo | Calibre traqueal y de la columna aérea faríngea. |
| Tejido adenoideo | Descriptivo | Relación adenoides-nasofaringe (opcional: cociente A/N). |
| Cociente adenoides/nasofaringe | Medición, opcional | Opcional (método de Fujioka). |
| Partes blandas prevertebrales | Descriptivo | Grosor prevertebral. |
| Cuerpos extraños | Descriptivo |  |
| Otros hallazgos | Descriptivo | Hallazgos incidentales o fuera de los apartados anteriores. |

