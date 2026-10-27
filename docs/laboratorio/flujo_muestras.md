# Registro de muestras por solicitud

La solicitud indica **qué estudios se piden**. Después, el personal registra la
muestra tomada o recibida e indica **cuáles de esos estudios usan esa muestra**.
Una muestra puede quedar vinculada con varios estudios de la misma solicitud.
Si hacen falta muestras diferentes, se registran por separado.

`POST /laboratorio/solicitudes/{solicitud_id}/muestras` recibe `estudio_ids`,
`tipo_muestra`, `fecha_toma`, `hora_toma` y `hora_no_registrada`. La API comprueba
que todos los estudios pertenecen a la solicitud, al mismo paciente y siguen
pendientes de muestra. Un solo registro en `muestra` se vincula con los estudios
seleccionados mediante `muestra_estudio`; sus estados avanzan juntos dentro de
la transacción HTTP. El endpoint anterior por estudio se conserva para clientes
existentes y usa la misma operación con un único estudio.

El tipo de muestra es texto libre porque los tipos y recipientes concretos deben
validarse con el hospital. El formulario no asume que todos los estudios de una
solicitud usan una misma muestra: la selección debe ser explícita. No se cambió
el esquema de la base de datos.
