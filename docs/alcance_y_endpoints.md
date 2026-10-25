
# Alcance, Hipótesis y Definición de Endpoints

> La planificación completa del Hito 1 está en [`hito1_plan.md`](./hito1_plan.md). Este documento conserva el contrato técnico resumido.

## Hipótesis y Supuestos (Alcance)
1. Un médico no puede tener dos turnos superpuestos; un paciente no puede tener dos turnos activos simultáneos con el mismo médico.
2. Si el paciente no hace check-in hasta 15 minutos después de la hora del turno, el turno queda como `ausente`.
3. La información persistente se aloja en MySQL mediante tablas relacionadas y consultas SQL explícitas.

## Restricciones Técnicas de la Cátedra
* **Base de Datos:** Está terminantemente prohibido el uso de ORMS (SQLAlchemy, SQLModel, Django ORM, Peewee u otros)[cite: 20]. La comunicación o consultas a la base de datos deben hacerse mediante sentencias SQL explícitas escritas en el código[cite: 20].
* **Comunicación Front/Back:** Está terminantemente prohibido utilizar funcionalidades que generen peticiones al front o al back desde el navegador (fetch, promises, axios, XMLHttpRequest u otras equivalentes)[cite: 20]. La comunicación entre el frontend y el backend debe realizarse en Python, mediante la librería `requests`[cite: 20].
* **Formato de datos:** Los endpoints deberán ser realizados utilizando el verbo correcto y se utilizará el formato JSON para enviar o recibir información[cite: 20].

## Listado de Endpoints RESTful

> El equipo inicialmente propuso rutas como `/pacientes/<dni>`, `/medicos/<nombre>`,
> `/consultorios/<numero>` y filtros de turnos por estado. La revisión y equivalencia
> de esas rutas está documentada en [`hito1_plan.md`](./hito1_plan.md). Para evitar
> ambigüedad, los estados y filtros se expresan como parámetros de consulta y los
> recursos se identifican con IDs estables.

### Módulo Público / Pacientes
* **`GET /api/especialidades`**: Retorna el listado de especialidades médicas.
* **`GET /api/medicos?especialidad_id={id}`**: Retorna los médicos de una especialidad específica.
* **`GET /api/turnos/disponibles?medico_id={id}&fecha={YYYY-MM-DD}`**: Consulta la agenda y retorna franjas libres.
* **`POST /api/turnos`**: Asigna el paciente al turno y genera el QR de confirmación.
* **`PATCH /api/turnos/{id}/cancelacion`**: Cancela un turno reservado y libera su franja.

### Módulo Backoffice / Recepción
* **`POST /api/checkins`**: Recibe los datos del QR y valida la regla de tiempo para marcar `confirmado` o `ausente`.
* **`GET /api/recepcion/sala-espera?fecha={YYYY-MM-DD}`**: Retorna la lista del día ordenada por hora de llegada.
* **`GET /api/admin/estadisticas?desde={fecha}&hasta={fecha}`**: Retorna datos agrupados para el dashboard.