# Flujo de enfermería

## Alcance

El piloto permite que una cuenta con rol `enfermeria` busque pacientes activos, cree y edite sus propios borradores de admisión, y los publique explícitamente. El registro admite motivo y síntomas referidos, observaciones de enfermería, peso, talla, temperatura, frecuencias cardíaca y respiratoria, presión arterial, saturación de oxígeno y escala de dolor de 0 a 10. No contiene diagnóstico ni tratamiento.

Cada registro conserva la cuenta que lo creó y las cuentas/fechas de publicación. Los borradores solo se devuelven a su autora. Después de publicar, quedan inmutables y solo sus datos publicados aparecen en el endpoint de lectura médica. El sistema no los copia automáticamente a una nota SOAP; el médico los revisa y decide qué registrar en su consulta.

## Acceso

La revisión Alembic `20261107_0013` agrega el rol y la tabla `registro_enfermeria`; ejecútala con `python -m alembic upgrade head` desde `backend`. Una instalación nueva también incluye el rol en `database/schema.sql`.

Para una prueba manual local, crea una cuenta ficticia con `python -m scripts.preparar_enfermera_demo` desde `backend`. El script solicita la contraseña interactivamente, crea `enfermera_demo` solo si no existe y no altera una cuenta previa. La cuenta médico ficticia documentada en `scripts.preparar_medico_demo` puede leer los registros publicados desde la ficha y el formulario de nueva consulta.

## Rutas

- `GET /enfermeria/pacientes?buscar=...`: búsqueda de pacientes para enfermería.
- `POST /enfermeria/pacientes/{paciente_id}/registros`: crea un borrador.
- `PUT /enfermeria/registros/{registro_id}`: actualiza un borrador propio.
- `GET /enfermeria/pacientes/{paciente_id}/registros`: lista borradores propios y publicaciones propias.
- `POST /enfermeria/registros/{registro_id}/publicar`: publica un borrador propio.
- `GET /enfermeria/pacientes/{paciente_id}/publicados`: lectura para el rol médico; devuelve únicamente registros publicados.

La ausencia de una medición se conserva como `null`; no se reemplaza por cero. Publicar es una acción explícita y auditada. El médico ve quién publicó cada registro y cuándo.
