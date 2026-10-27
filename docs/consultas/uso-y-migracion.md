# Consulta médica (piloto con datos ficticios)

## Preparación

1. Configurar `backend/.env` con `DATABASE_URL` y `JWT_SECRET_KEY` y comprobar que apunta a la base esperada. No ejecutar `database/schema.sql` sobre una base existente.
2. Desde `backend/`, ejecutar `./.venv/Scripts/alembic.exe current` y `./.venv/Scripts/alembic.exe upgrade head`. La revisión `20261027_0007` añade `medico_especialidad.vigente`, impone una especialidad por médico y añade a `consulta` identidad del creador y clave UUID de reintento. No elimina filas ni la columna histórica `fecha_fin`. Si ya hay varias especialidades de un médico, la migración se cancela sin borrar ninguna: revisar los datos con el equipo antes de continuar.
3. Para poder registrar: debe existir un trabajador activo asociado a una cuenta activa de rol `medico`, una fila activa en `medico` y exactamente una asociación `medico_especialidad` con `vigente=true` y especialidad activa. El módulo **no** inventa especialidades ni asignaciones. Si una especialidad deja de estar vigente, un administrador deberá corregir el dato mediante el proceso de administración autorizado (aún sin pantalla en este piloto).
4. Se necesita al menos un paciente **ficticio** registrado; esta instalación puede no traer ninguno. No se crea ni copia un paciente al buscarlo. Las pruebas de integración crean filas ficticias dentro de una transacción y hacen rollback al terminar.

Iniciar backend desde `backend` con `./.venv/Scripts/python.exe -m uvicorn app.main:app` e iniciar frontend desde `frontend` con `npm run dev`. Entrar como médico y seleccionar **Consulta médica** en Inicio. Buscar por nombre, documento, historia o código; abrir ficha, revisar historial, elegir **Nueva consulta**, introducir motivo y diagnóstico manuales, confirmar el cierre, y volver a abrir el detalle desde la ficha. El número de consulta, médico y fecha los asigna el servidor.

## API

Todas las rutas requieren JWT de rol `medico`:

- `GET /consultas/pacientes?buscar=...&pagina=1&limite=20` (2–100 caracteres, máximo 30 por página).
- `GET /consultas/pacientes/{paciente_id}`.
- `GET /consultas/pacientes/{paciente_id}/historial?pagina=1&limite=20`.
- `GET /consultas/{consulta_id}`.
- `POST /consultas` con `paciente_id`, `clave_idempotencia` UUID, `motivo_consulta` y `diagnostico_principal` obligatorios; otros campos SOAP opcionales. Primera creación: 201; mismo UUID y contenido del mismo actor: 200 sin duplicar; UUID con contenido distinto: 409.

Una consulta cerrada no se edita. Todos los médicos autorizados pueden leer consultas anteriores, incluso las abiertas y anuladas. La auditoría de creación se guarda en la misma transacción, sin narrativas clínicas en el log. IMC se calcula para mostrarlo, no se registra si falta peso o talla.

## Pruebas y límites

- `cd backend; ./.venv/Scripts/python.exe -m pip check; ./.venv/Scripts/python.exe -m pytest -q` (incluye PostgreSQL para `test_consultas_integracion.py`).
- `cd frontend; node --test src/features/consultas/utils/formulario.test.js; npm run lint; npm run build`.
- La integración PostgreSQL de pruebas autentica una cuenta médica ficticia, busca paciente ficticio, registra, reintenta, detecta conflicto, consulta historial y verifica auditoría. No deja filas clínicas persistentes de prueba.
- Verificación local del 27/10/2026: `pytest -q` 48/48, `pip check` sin problemas, `node --test` 6/6 (incluye 3 pruebas existentes de Laboratorio), `npm run lint` correcto, `npm run build` correcto, importación de `app.main` y `/health` correctos; Alembic en `20261027_0007`. Falta la comprobación manual del formulario en navegador con una cuenta médica y un paciente de prueba **persistentes**: la base local tiene usuarios de Laboratorio, pero todavía no tiene médicos, especialidades ni pacientes. La prueba automatizada de extremo a extremo se revierte al terminar y no los provisiona de forma permanente.
- Figma no estaba accesible; se siguió la identidad visual del módulo Laboratorio. Enfermería y sus registros están fuera del alcance; el médico introduce únicamente los datos disponibles. Tampoco se implementan borradores, correcciones históricas, selección automática de CIE-10, dictado ni recetas farmacéuticas.
- El formulario mantiene los campos SOAP por nombre y el estado centralizado; una futura transcripción podrá proponer valores por campo para **revisión humana**, sin enviar, diagnosticar ni finalizar automáticamente.
