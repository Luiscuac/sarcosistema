# Migraciones de laboratorio

Las bases SarcoSistema existentes fueron inicializadas con `database/schema.sql`. Ese archivo es el bootstrap de una base nueva; no debe volver a ejecutarse sobre una base que ya contiene datos.

Los modelos ORM todavía representan solo una parte de las 52 tablas. Por eso, las revisiones se escriben y revisan explícitamente. El filtro de Alembic ignora objetos existentes que el ORM aún no mapea para evitar que el autogenerador sugiera borrarlos; cada migración generada debe revisarse antes de aplicarse.

## Qué prepara la primera migración de laboratorio

- Relaciona cada `tipo_estudio` con una `plantilla_examen` opcional. Se deja opcional para poder migrar sin asignar formatos no validados.
- Añade precisión decimal opcional a cada parámetro. `NULL` significa que el laboratorio todavía no confirmó la precisión.
- Añade opciones configurables para resultados cualitativos.
- Añade un campo opcional para el tipo de muestra, sin imponer nombres u opciones clínicas.
- No inserta parámetros, rangos ni valores de paciente.

Las referencias leídas del D-9 siguen siendo transcripciones en el catálogo de trabajo. Se deben cargar en las plantillas, versionadas, después de que el laboratorio confirme que son las referencias vigentes.

## Aplicar en una base que ya tiene el esquema

1. Hacer un respaldo de la base de desarrollo.
2. Activar el entorno virtual del backend.
3. Desde `backend/`, comprobar que el `DATABASE_URL` del entorno apunta a la base de desarrollo correcta.
4. Ejecutar `alembic upgrade head`.
5. Comprobar con `alembic current` que la revisión activa sea `20261027_0006`.

La revisión `20261022_0001` es una comprobación de que existe el esquema base esperado. No recrea tablas ni modifica datos. `20261022_0003` agrega cuatro prestaciones del D-8 si sus códigos no existen: hemograma completo, examen general de orina, coproparasitológico simple y seriado. No activa plantillas ni fija valores clínicos; las prestaciones sí quedan disponibles para crear solicitudes.

## Base nueva

En una base nueva, el bootstrap definido por el procedimiento de desarrollo crea el esquema base. Luego se ejecuta `alembic upgrade head` para aplicar las extensiones incrementales. No se debe apuntar a una base con datos reales desde el entorno local.

## Catálogo inicial de resultados

La revisión `20261022_0004` carga formatos activos para hemograma, examen general de orina, coproparasitología simple/seriada y química sanguínea. Incluye únicamente los campos transcritos en `catalogo-parametros-para-validacion.md`; el campo ilegible de orina se omite. Química sanguínea se carga como un panel con los parámetros y referencias transcritos por el equipo.

Las referencias se guardan como texto y no se usan para rechazar valores ni marcar resultados automáticamente fuera de rango. La precisión decimal queda sin fijar y los campos cualitativos aceptan texto libre porque todavía no se confirmaron las opciones impresas. Esta carga habilita el flujo de desarrollo/demostración; no equivale a una validación institucional ni a autorización para producción clínica. Revisar los formularios originales con el laboratorio antes de desplegar en uso real.

Para una base que ya está en `20261022_0003`, aplicar desde `backend/`:

```powershell
alembic upgrade head
alembic current
```

La revisión agrega el tipo `QUIMICA_SANGUINEA` si falta, crea las plantillas y las relaciona con los tipos de estudio. No vuelve a ejecutar `database/schema.sql` ni borra datos existentes.

## Registro mensual de 2026

La revisión `20261026_0005` añade a `paciente` los campos opcionales `historia_clinica` y `codigo_externo`. El código interno `codigo_paciente` permanece independiente. Añade a `tipo_estudio` una categoría de laboratorio y prestaciones transcritas de los **encabezados** del registro mensual. No importa filas ni datos personales del archivo.

Se agrupan prestaciones en Hematología, Bioquímica, Serología y Copro y orina. El significado y las reglas de unicidad de los dos identificadores externos, la clasificación de algunas pruebas y el catálogo completo deben confirmarse con el hospital. Se dejaron fuera las pruebas de microbiología que no encajan en los cuatro grupos indicados; no se asignaron a una categoría arbitraria.

## Captura libre para la demostración

La revisión `20261027_0006` añade una plantilla individual de versión 1 a las 32 prestaciones de esos grupos que aún no tenían formato. Contiene `Resultado` obligatorio y `Unidad (si aplica)` opcional; no inventa valores normales ni opciones clínicas. Las cinco prestaciones con formato detallado conservan sus parámetros. La captura libre permite demostrar el flujo completo y queda guardada con la versión de su plantilla.

Cuando el hospital entregue los parámetros, crear una versión nueva de la plantilla correspondiente y activar esa versión. No modificar una versión usada por resultados anteriores. La captura libre es una decisión provisional para el prototipo; la institución debe confirmar el formato de cada prestación antes de usarlo con datos clínicos reales.

La revisión es aditiva. Antes de aplicarla a una base con datos, crear y comprobar un respaldo. Después ejecutar desde `backend/`:

```powershell
alembic upgrade head
alembic current
```

La revisión activa debe ser `20261027_0006`.
