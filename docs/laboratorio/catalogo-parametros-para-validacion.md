# Catálogo inicial de laboratorio

**Estado:** transcripción de trabajo basada en la lectura del equipo de los formularios D-8/D-9 y la foto compartida.
**Rama:** `feature/laboratorio`.
**Uso:** especificación para diseñar la migración y las pantallas; las referencias se deben confirmar con el laboratorio antes de usarlas como valores clínicos del sistema.

No se copiaron datos personales ni resultados del paciente que aparecen en la fotografía. Los valores de referencia que siguen son los que el equipo alcanzó a leer en el formulario, no rangos recomendados por este proyecto.

## 1. Formularios y flujo

### D-8: solicitud de exámenes

El D-8 es el pedido que inicia el proceso. La aplicación debe capturar su información en un flujo guiado:

1. Identificar o registrar al paciente.
2. Registrar los datos del pedido: fecha, establecimiento y profesional solicitante, diagnóstico si figura, referencia de papel y prioridad.
3. Seleccionar uno o varios estudios del catálogo.
4. Confirmar la solicitud y mostrarla en la bandeja de pendientes.

El formulario incluye también imagenología y banco de sangre. En el incremento de laboratorio se digitalizarán las solicitudes de laboratorio; las otras secciones quedan para sus módulos correspondientes.

### D-9: reporte de resultados

El D-9 es el informe que se completa después de procesar los estudios. Comparte la referencia del pedido D-8. En el sistema corresponde al flujo de registrar muestra, capturar resultados, guardar borrador, revisar, publicar y emitir/imprimir el reporte.

Una solicitud puede agrupar varios estudios; cada estudio conserva su propio estado y resultado. Esto permite publicar un estudio terminado sin marcar como terminado otro que sigue pendiente.

## 2. Hemograma

Los nombres expandidos se muestran junto con las abreviaturas que se distinguen en el formulario. El usuario confirma `CAY` (cayados) como parámetro del diferencial. Un campo adicional que no se alcanza a leer queda omitido.

| Parámetro | Abreviatura | Unidad leída | Estado |
| --- | --- | --- | --- |
| Glóbulos rojos | GR | mm³ (el formulario parece indicar cantidad por mm³) | Confirmar escala/unidad completa |
| Glóbulos blancos | GB | mm³ (el formulario parece indicar cantidad por mm³) | Confirmar escala/unidad completa |
| Hematocrito | Hto. | % | Lectura probable; confirmar nombre impreso |
| Hemoglobina | Hb | g/dL | Lectura del equipo |
| Plaquetas | — | mm³ (cantidad por mm³) | Confirmar escala/unidad completa |
| Segmentados | SEG | % | Lectura del equipo |
| Linfocitos | LIN | % | Lectura del equipo |
| Eosinófilos | EOS | % | Lectura del equipo |
| Basófilos | BAS | % | Lectura del equipo |
| Monocitos | MON | % | Lectura del equipo |
| Cayados | CAY | % | Confirmado por el usuario |

## 3. Química sanguínea

Se transcriben las referencias impresas que se alcanzan a leer. La forma de comparación (`entre`, `menor que`, `mayor que` o `hasta`) debe conservarse como parte de la referencia.

| Estudio/parámetro | Referencia leída | Unidad | Estado |
| --- | --- | --- | --- |
| Ácido úrico | 2.4–7.0 | mg/dL | Transcrito de D-9; confirmar |
| Glicemia | 70–115 | mg/dL | Transcrito de D-9; confirmar si el estudio es basal |
| Creatinina sérica | 0.6–1.3 | mg/dL | Transcrito de D-9 |
| Colesterol total | Menor a 190 | mg/dL | Transcrito de D-9 |
| HDL-colesterol | Mayor a 45 | mg/dL | Transcrito de D-9 |
| LDL-colesterol | Menor a 190 | mg/dL | Lectura del usuario; confirmar contra original nítido |
| Triglicéridos | Hasta 200 | mg/dL | Transcrito de D-9 |
| Urea | 10–50 | mg/dL | Transcrito de D-9 |
| BUN | 10–20 | mg/dL | Lectura probable; confirmar nombre y rango |
| Transaminasa GOT | Hasta 37 | U/L | Transcrito de D-9 |
| Transaminasa GPT | Hasta 42 | U/L | Transcrito de D-9 |
| Bilirrubina directa | Hasta 0.2 | mg/dL | Transcrito de D-9 |
| Bilirrubina indirecta | Hasta 0.8 | mg/dL | Transcrito de D-9 |
| Bilirrubina total | Hasta 1.0 | mg/dL | Transcrito de D-9 |

En el D-8 los análisis aparecen como prestaciones seleccionables (por ejemplo, glicemia basal, creatinina sérica, transaminasas y perfil lipídico). En el D-9 se muestran varios resultados juntos. Antes de modelar el catálogo hay que confirmar qué prestaciones del pedido corresponden a qué paneles de resultados. No asumir que toda química sanguínea se pide o procesa como un único estudio.

## 4. Examen general de orina

### Examen físico y químico — columna de resultados

| Parámetro | Tipo sugerido para captura | Unidad/referencia |
| --- | --- | --- |
| Color | Selección o texto | Por confirmar |
| Olor | Selección o texto | Por confirmar |
| Aspecto | Selección o texto | Por confirmar |
| Densidad | Decimal o texto según formato | Por confirmar |
| pH | Decimal | Por confirmar |
| Proteínas | Cualitativo | Opciones por confirmar |
| Hemoglobina | Cualitativo | Opciones por confirmar |
| Glucosa | Cualitativo | Opciones por confirmar |
| Cetonas | Cualitativo | Opciones por confirmar |
| Urobilina | Cualitativo | Opciones por confirmar; confirmar rótulo exacto (¿urobilina/urobilinógeno?) |
| Nitritos | Cualitativo | Opciones por confirmar |
| Leucocitos | Cualitativo | Opciones por confirmar |
| Bilirrubina | Cualitativo | Opciones por confirmar |

### Examen microscópico — columna de resultados

| Parámetro | Tipo sugerido para captura | Unidad/referencia |
| --- | --- | --- |
| Células epiteliales | Texto o rango | Por confirmar |
| Células de transición | Texto o rango | Por confirmar |
| Células redondas | Texto o rango | Por confirmar |
| Leucocitos | Texto o rango | Por confirmar |
| Eritrocitos | Texto o rango | Por confirmar |
| Flora bacteriana | Cualitativo/texto | Opciones por confirmar |
| Filamentos mucoides | Cualitativo/texto | Lectura probable del usuario; confirmar grafía |
| Trichomonas vaginalis | Cualitativo/texto | Confirmar rótulo exacto del formulario |
| Cilindros granulosos | Texto o rango | Por confirmar |
| Cilindros hialinos | Texto o rango | Por confirmar |
| Cristales | Texto estructurado | Tipos/opciones por confirmar |
| Campo ilegible | Omitido | No agregar hasta leer el original |

## 5. Coproparasitología

Se conserva el catálogo ya revisado por el usuario.

### Examen macroscópico

- Color
- Consistencia
- Restos alimenticios
- Otros

### Examen microscópico

- Hallazgo parasitológico
- Flora bacteriana
- Leucocitos
- Eritrocitos

Los tipos de captura, unidades y opciones se confirmarán contra el formato del servicio.

## 6. Otros estudios visibles en D-8

El D-8 muestra una lista más amplia que los cuatro formatos desarrollados en este documento. Entre los rótulos legibles aparecen: ácido úrico, amilasa pancreática, baciloscopía diagnóstica y de seguimiento, bilirrubinas, colesterol total, coproparasitológico seriado y simple, creatinina en orina y sérica, cultivo/antibiograma, electrolitos, ELISA para Chagas, examen general de orina, factor reumatoideo, fosfatasa ácida/alcalina, glicemia basal y postprandial, grupo sanguíneo/Rh, hemaglutinación indirecta para Chagas, hemoglobina/hematocrito, hemoglobina glicosilada, hemograma completo, nitrógeno ureico/urea, perfil lipídico, proteína C reactiva, proteinuria de 24 horas, pruebas de tolerancia a glucosa, pruebas rápidas, reacción de Widal, RPR/VDRL, tiempo de sangría/coagulación, tinción Gram, transaminasas y velocidad de eritrosedimentación.

La fotografía no permite verificar con seguridad cada palabra ni constituye un catálogo exhaustivo. Estos rótulos son candidatos a prestaciones del D-8; se deben transcribir desde una copia limpia antes de incorporarlos. En particular, no se deben inventar parámetros ni referencias para esos estudios.

## 7. Datos por confirmar antes de cargar resultados

1. Nombre oficial y código de cada prestación solicitada.
2. Relación entre una prestación del D-8 y uno o más parámetros del D-9.
3. Escala/unidad exacta de GR, GB y plaquetas (por ejemplo, valor absoluto por mm³ o forma abreviada impresa).
4. Que Hto. sea hematocrito y que el diferencial incluya CAY.
5. Rótulos exactos de orina: urobilina/urobilinógeno, filamentos mucoides y Trichomonas vaginalis.
6. Nombre y rango de BUN, LDL y demás referencias dudosas.
7. Opciones cualitativas, precisión decimal, valores permitidos y obligatoriedad por campo.
8. Si las referencias dependen de edad, sexo u otra condición, y cómo las versiona el servicio.
9. Cuáles resultados son obligatorios para guardar borrador, revisar o publicar.
10. Formato impreso del D-9, firmas, sellos y fecha/hora que deben incluirse.

## 8. Modelo de datos esperado

Los parámetros clínicos deben ser filas configurables, no columnas nuevas por análisis:

```text
tipo_estudio → plantilla_examen → plantilla_examen_version
                                  ├── seccion_plantilla
                                  └── parametro_plantilla
resultado_laboratorio → version_resultado → detalle_valor_resultado
```

El esquema actual ya contiene estas entidades genéricas. La etapa de base de datos debe revisar si hace falta agregar la relación entre `tipo_estudio` y plantilla, opciones para campos cualitativos, referencias versionadas y datos de recepción/rechazo de muestra. Se debe hacer mediante Alembic y datos de catálogo separados; nunca volver a ejecutar `schema.sql` sobre la base existente.

## 9. Alcance de la primera entrega

Orden recomendado para cerrar el flujo vertical:

1. Bandeja y solicitud desde D-8 para laboratorio.
2. Identificación del paciente y solicitud con uno o más estudios.
3. Muestra y estados pendientes.
4. Captura de resultado basada en plantillas.
5. Borrador, revisión, publicación parcial y auditoría.
6. Consulta/impresión con formato derivado del D-9.
7. Rectificación versionada y pruebas del flujo.

La lista amplia de servicios del D-8 se implementará progresivamente. Para el primer recorrido se priorizan hemograma, química sanguínea, examen general de orina y coproparasitología, una vez que el laboratorio confirme los formatos.
