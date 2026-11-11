
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

### Módulo Público y Autenticación (Sin sesión previa)
* **`GET /api/especialidades`**: Retorna el listado de especialidades médicas (público, sin login).
* **`GET /api/medicos?especialidad={id}`**: Retorna los médicos activos de una especialidad específica (público, sin login).
* **`GET /api/turnos/disponibles?medico={id}&fecha={fecha}`**: Consulta la agenda y retorna los turnos en estado “disponible” de ese médico y día **sin requerir inicio de sesión**.
* **`POST /api/pacientes`**: Registra un paciente nuevo (`dni` de 7-8 dígitos, `nombre` <= 100 chars, `apellido` <= 100 chars, `email` <= 254 chars, `password` de 8-128 chars). El servidor asigna siempre `rol = "paciente"` y `activo = 1`, y almacena la contraseña con el hash canónico `pbkdf2:sha256:600000` (`salt_length=12`, 98 caracteres, compatible con `password_hash VARCHAR(255)` de `db.sql`). Devuelve `201 Created`, `400 Bad Request` ante datos inválidos o campos no permitidos, y `409 Conflict` si el DNI o email ya existen.
* **`POST /api/auth/login`**: Autentica un usuario activo mediante `email` y `password`. Verifica hashes de `werkzeug.security` (`pbkdf2:` / `scrypt:`) y migra de forma transparente al formato canónico los hashes PBKDF2 de `feature/pacientes` (`<32-hex-salt>$<64-hex-sha256>`), rechazando siempre contraseñas en texto plano. Devuelve `200 OK` con `access_token` (JWT firmado con `HS256`), `token_type: "Bearer"`, `expires_in` y los datos públicos del usuario (`id`, `id_usuario`, `dni`, `nombre`, `apellido`, `email`, `rol`), o `401 Unauthorized` con mensaje uniforme (`"Credenciales inválidas."`) si el email no existe, la contraseña no coincide o la cuenta está inactiva.

### Autenticación JWT, Sesión Server-Side y Protección de Rutas Privadas
* **Transporte:** El frontend consume los endpoints protegidos desde Python (`requests`) enviando el encabezado `Authorization: Bearer <access_token>`.
* **Algoritmo y clave:** Firma simétrica explícita con `HS256` y clave leída exclusivamente desde la variable de entorno `JWT_SECRET_KEY` (mínimo 32 caracteres). Al decodificar solo se acepta `HS256`.
* **Claims obligatorios del token:**
  * `sub`: `id_usuario` (`usuarios.id`) representado como string (estándar RFC 7519).
  * `id_usuario`: identificador entero del usuario autenticado (`usuarios.id`, que coincide con la FK `turnos.id_usuario`).
  * `dni`: DNI del usuario autenticado (`usuarios.dni`).
  * `iat` y `exp`: marcas de emisión y expiración (vencimiento corto configurable mediante `JWT_EXPIRATION_SECONDS`, por defecto `3600` segundos / 1 hora).
* **Tratamiento del DNI, sesión server-side y privacidad del token:** Un JWT firmado (JWS) garantiza integridad y autenticidad pero **no está cifrado** (su payload es Base64URL legible por quien posea el token). Por ello:
  1. Solo se incluyen `sub`, `id_usuario`, `dni`, `iat` y `exp`, sin agregar datos personales adicionales (`email`, `nombre`, `apellido`, etc.) ni registrar el token en logs.
  2. El frontend utiliza `FileSystemSessionInterface` (`frontend/services/session_store.py`) para almacenar del lado del servidor `session["id_usuario"]` (`usuarios.id`), `session["dni"]` (`usuarios.dni`), `session["access_token"]`, `session["usuario"]` y `session["_expires_at"]`, enviando al navegador únicamente una cookie (`cmsi_session`) con un identificador aleatorio firmado (`HttpOnly`, `SameSite=Lax`, `Secure` cuando `FRONTEND_COOKIE_SECURE=1`) que se regenera al iniciar sesión.
* **Alcance del logout y vencimiento del JWT:** Al cerrar sesión (`POST /auth/logout`), el frontend elimina inmediatamente el archivo de sesión server-side y la cookie del navegador. El backend no mantiene una lista de revocación de tokens emitidos: si un JWT hubiera sido copiado antes del logout, seguiría siendo criptográficamente válido hasta su `exp` (`3600` s por defecto), salvo que la cuenta sea dada de baja (`activo = 0`), lo cual invalida el acceso en el acto porque cada petición protegida consulta el estado actual en MySQL.
* **Derivación de identidad y estado de protección por módulo:** Ningún endpoint privado confía en un `id_usuario` o `dni` enviado libremente por el cliente como prueba de identidad; la identidad se extrae de los claims validados del JWT y se contrasta en MySQL (`SELECT ... FROM usuarios WHERE id = %s AND dni = %s`).
  * **Públicos (sin inicio de sesión):** `GET /api/especialidades`, `GET /api/medicos`, `GET /api/medicos/{id}`, `GET /api/consultorios`, `GET /api/consultorios/{id}`, `GET /api/turnos/disponibles?medico={id}&fecha={fecha}`, `POST /api/pacientes` y `POST /api/auth/login`.
  * **Protegidos para `paciente` / `admin` (con control de titularidad):**
    * `GET /api/auth/me`: requiere JWT válido y cuenta activa (`paciente` o `admin`).
    * `GET /api/pacientes/{dni}` y `PATCH /api/pacientes/{dni}`: requieren JWT válido (`paciente` o `admin`) y verifican en el servidor que `g.usuario_actual["dni"] == dni` o `g.usuario_actual["rol"] == "admin"` (`403 Forbidden` en caso contrario).
    * `POST /api/turnos/reservar`: requiere JWT válido con `rol = "paciente"`, tomando `id_usuario` exclusivamente del token.
    * `PATCH /api/turnos/{id}/cancelar`, `GET /api/turnos` y `GET /api/turnos/{id}`: requieren JWT válido (`paciente` o `admin`); cuando consulta un `paciente`, solo puede operar o listar sus propios turnos (`403 Forbidden` ante un DNI o turno ajeno).
  * **Protegidos exclusivamente para `admin` (Recepción y Backoffice):**
    * `GET /api/pacientes` y `PATCH /api/pacientes/{dni}/baja`.
    * `POST /api/turnos`, `POST /api/turnos/checkin`, `GET /api/turnos/sala-espera` y `PATCH /api/turnos/{id}/atender`.
    * `POST /api/especialidades`, `POST /api/consultorios`, `PATCH /api/consultorios/{id}`, `PATCH /api/consultorios/{id}/baja`, `POST /api/medicos`, `PATCH /api/medicos/{id}` y `PATCH /api/medicos/{id}/baja`.

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
