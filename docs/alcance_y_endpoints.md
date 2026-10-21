
# Alcance, Hipótesis y Definición de Endpoints

## Hipótesis y Supuestos (Alcance)
1. Un médico no puede tener dos turnos superpuestos; un paciente no puede tener dos turnos activos simultáneos con el mismo médico[cite: 18].
2. Si el paciente no hace check-in dentro de la ventana permitida (por ejemplo, hasta 15 minutos después de la hora del turno), el turno queda como "ausente"[cite: 18].
3. Todo el catálogo de información se aloja en MySQL mediante al menos 3 tablas core interrelacionadas[cite: 20].

## Restricciones Técnicas de la Cátedra
* **Base de Datos:** Está terminantemente prohibido el uso de ORMS (SQLAlchemy, SQLModel, Django ORM, Peewee u otros)[cite: 20]. La comunicación o consultas a la base de datos deben hacerse mediante sentencias SQL explícitas escritas en el código[cite: 20].
* **Comunicación Front/Back:** Está terminantemente prohibido utilizar funcionalidades que generen peticiones al front o al back desde el navegador (fetch, promises, axios, XMLHttpRequest u otras equivalentes)[cite: 20]. La comunicación entre el frontend y el backend debe realizarse en Python, mediante la librería `requests`[cite: 20].
* **Formato de datos:** Los endpoints deberán ser realizados utilizando el verbo correcto y se utilizará el formato JSON para enviar o recibir información[cite: 20].

## Listado de Endpoints RESTful

### Módulo Público / Pacientes
* **`GET /api/especialidades`**: Retorna el listado de especialidades médicas.
* **`GET /api/medicos?especialidad={id}`**: Retorna los médicos de una especialidad específica.
* **`GET /api/turnos/disponibles?medico={id}&fecha={fecha}`**: Consulta la agenda y retorna franjas libres.
* **`POST /api/turnos/reservar`**: Asigna el paciente al turno, genera el QR y gatilla el envío de email[cite: 18].
* **`POST /api/turnos/cancelar`**: Libera un turno reservado.

### Módulo Backoffice / Recepción
* **`POST /api/checkin/escanear`**: Recibe los datos del QR y valida la regla de tiempo para marcar "confirmado" o "ausente"[cite: 18].
* **`GET /api/recepcion/sala-espera`**: Retorna la lista del día ordenada por orden de llegada (check-in)[cite: 19].
* **`GET /api/admin/estadisticas`**: Retorna datos agrupados para el dashboard (ocupación, especialidades más pedidas, porcentaje de ausentismo)[cite: 19].