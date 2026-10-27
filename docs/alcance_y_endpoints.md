
# Alcance, Hipótesis y Definición de Endpoints

> La planificación completa del Hito 1 está en [`hito1_plan.md`](./hito1_plan.md). Este documento conserva el contrato técnico resumido.

## Hipótesis y Supuestos (Alcance)
1. Un médico no puede tener dos turnos superpuestos; un paciente no puede tener dos turnos activos simultáneos con el mismo médico.
2. Si el paciente no hace check-in hasta 15 minutos después de la hora del turno, el turno queda como `ausente`.
3. La información persistente se aloja en MySQL mediante tablas relacionadas y consultas SQL explícitas.
4. **Relación Médicos - Especialidades / Obras Sociales:** Un médico puede asociarse a una o más especialidades mediante una tabla intermedia `medicos_especialidades` (relación N:M, extensible también a coberturas/obras sociales si se requiere).
5. **Tabla unificada `usuarios` y unificación de rol `admin`:** Los datos de autenticación (`email`, `password_hash`, `rol`) y los datos personales (`dni`, `nombre`, `apellido`, `activo`) se unifican en una sola tabla `usuarios`. El campo `rol` admite dos perfiles autenticados: `paciente` y `admin` (este último unifica las tareas operativas de recepción y las de backoffice/administración de la clínica).
6. Hay una sola sede del centro médico.
7. Recepción se encarga de escanear el QR del paciente.
8. Todos los turnos médicos tienen una duración de 30 minutos.
9. **Acceso Público sin Login (Usuario no logueado):** Cualquier visitante no autenticado puede navegar el portal público para:
   - Consultar especialidades, médicos activos y **turnos disponibles sin necesidad de iniciar sesión** (`GET /api/turnos/disponibles`). El inicio de sesión o registro se exige recién al confirmar la reserva (`POST /api/turnos/reservar`).
   - Visualizar secciones informativas del centro médico: **Novedades**, **Ofertas / Campañas de salud** (chequeos preventivos, vacunación, aptos físicos), **Ubicación y Mapa interactivo** de la sede, horarios de atención y canales de contacto.

## Restricciones Técnicas de la Cátedra
* **Base de Datos:** Está terminantemente prohibido el uso de ORMS (SQLAlchemy, SQLModel, Django ORM, Peewee u otros)[cite: 20]. La comunicación o consultas a la base de datos deben hacerse mediante sentencias SQL explícitas escritas en el código[cite: 20].
* **Comunicación Front/Back:** Está terminantemente prohibido utilizar funcionalidades que generen peticiones al front o al back desde el navegador (fetch, promises, axios, XMLHttpRequest u otras equivalentes)[cite: 20]. La comunicación entre el frontend y el backend debe realizarse en Python, mediante la librería `requests`[cite: 20].
* **Formato de datos:** Los endpoints deberán ser realizados utilizando el verbo correcto y se utilizará el formato JSON para enviar o recibir información[cite: 20].

## Listado de Endpoints RESTful

### Módulo Público (Sin ingreso / Sin autenticación)
* **`GET /api/especialidades`**: Retorna el listado de especialidades médicas (público, sin login).
* **`GET /api/medicos?especialidad={id}`**: Retorna los médicos activos de una especialidad específica (público, sin login).
* **`GET /api/turnos/disponibles?medico={id}&fecha={fecha}`**: Consulta la agenda y retorna los turnos en estado “disponible” de ese médico y día **sin requerir inicio de sesión**.
* **`POST /api/pacientes`**: Registra un paciente nuevo (DNI, nombre y apellido, mail, contraseña).

### Módulo Pacientes (Con ingreso / Autenticado)
* **`POST /api/turnos/reservar`**: Asigna el paciente autenticado al turno, lo pasa a “reservado”, genera el QR y envía el email con el botón cancelar.
* **`PATCH /api/turnos/{id}/cancelar`**: Pasa el turno a “cancelado” y lo libera.
* **`GET /api/pacientes/{dni}`**: Retorna el perfil del paciente (solo el propio).
* **`PATCH /api/pacientes/{dni}`**: Modifica nombre o mail del paciente (solo el propio).
* **`GET /api/turnos?dni={dni}`**: Retorna los turnos de un paciente (solo los propios).

### Módulo Recepción
* **`POST /api/turnos/checkin`**: Recibe los datos del QR y valida la ventana de 15 minutos para marcar “confirmado” o “ausente”.
* **`GET /api/turnos/sala-espera`**: Retorna los turnos “confirmados” del día en sala de espera.
* **`PATCH /api/turnos/{id}/atender`**: Marca el turno como “atendido”.

### Módulo Backoffice / Administración

#### ABM de especialidades
* **`GET /api/especialidades`**: Retorna el listado de especialidades médicas.
* **`POST /api/especialidades`**: Alta de especialidad.

#### ABM de médicos
* **`GET /api/medicos`**: Retorna el listado de médicos (activos e inactivos).
* **`GET /api/medicos/{id}`**: Retorna el detalle de un médico.
* **`POST /api/medicos`**: Alta de médico.
* **`PATCH /api/medicos/{id}`**: Modifica nombre, especialidad o consultorio.
* **`PATCH /api/medicos/{id}/baja`**: Da de baja un médico.

#### ABM de consultorios
* **`GET /api/consultorios`**: Retorna el listado de consultorios.
* **`GET /api/consultorios/{id}`**: Retorna el detalle de un consultorio.
* **`POST /api/consultorios`**: Alta de consultorio.
* **`PATCH /api/consultorios/{id}`**: Modifica el consultorio.
* **`PATCH /api/consultorios/{id}/baja`**: Da de baja un consultorio.

#### ABM de pacientes
* **`GET /api/pacientes`**: Retorna el listado de pacientes.
* **`PATCH /api/pacientes/{dni}/baja`**: Da de baja un paciente.

#### Gestión de turnos y agenda
* **`POST /api/turnos`**: Crea un turno en estado “disponible” para un médico en una fecha y hora.
* **`GET /api/turnos`**: Retorna el listado de turnos.
* **`GET /api/turnos?medico={id}`**: Retorna los turnos de un médico.
* **`GET /api/turnos?estado={estado}`**: Filtra los turnos por estado (disponible, reservado, confirmado, atendido, cancelado, ausente).
* **`GET /api/turnos/{id}`**: Retorna el detalle de un turno.
