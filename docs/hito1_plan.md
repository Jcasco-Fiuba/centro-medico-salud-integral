# Hito 1 - Planificación del sistema

## 1. Identificación del proyecto

**Nombre:** Centro Médico Salud Integral  
**Producto:** plataforma web para reservar turnos médicos y gestionar la atención presencial.  
**Usuarios principales:** pacientes y personal administrativo/recepción.  
**Equipo:** Grupo 18 - Seguidores del Loro Matteoli & larp.

## 2. Problema

El centro médico necesita coordinar agendas de varios profesionales y especialidades. Cuando la reserva, la confirmación de llegada y la atención se gestionan por canales separados, aparecen problemas concretos:

- el paciente no conoce fácilmente los horarios disponibles;
- recepción debe confirmar manualmente quién llegó y en qué orden;
- se producen turnos superpuestos o reservas duplicadas;
- las cancelaciones y ausencias no quedan registradas de forma uniforme;
- no hay indicadores confiables para conocer ocupación y ausentismo.

Estos problemas generan demoras, trabajo administrativo repetido y pérdida de disponibilidad por turnos reservados que finalmente no se utilizan.

## 3. Solución propuesta

Desarrollar una plataforma web con tres niveles de experiencia:

1. **Portal Público (Usuario no logueado):** página de inicio informativa con secciones de **Novedades**, **Ofertas / Campañas preventivas**, **Ubicación con mapa interactivo y horarios de atención**, cartilla de especialidades/profesionales y **consulta pública de turnos disponibles sin necesidad de iniciar sesión** (`GET /api/turnos/disponibles`).
2. **Portal de Pacientes (Autenticado):** registro e inicio de sesión para confirmar la reserva del turno seleccionado, recepción de confirmación por email con código QR y botón de cancelación, consulta de turnos propios y edición de perfil.
3. **Backoffice de Recepción / Administración:** gestión (ABM) de especialidades, médicos, consultorios, pacientes y generación de turnos disponibles en agenda; escaneo del QR en recepción (`checkin`) y gestión de la sala de espera.

La solución estará compuesta por un frontend server-side en Flask, un backend REST en Flask y una base MySQL. La comunicación frontend-backend se realizará desde Python mediante `requests`, de acuerdo con las restricciones de la cátedra. Las consultas a MySQL se escribirán con SQL explícito, sin ORM.

## 4. Objetivo general

Centralizar la gestión de turnos del centro médico para que cualquier visitante pueda consultar información y disponibilidad de forma pública, los pacientes registrados puedan reservarlos de forma clara, y el personal pueda controlar la llegada, la atención y la administración del centro.

## 5. Objetivos específicos

- Brindar una vista pública enriquecida para usuarios no logueados (novedades, ofertas/campañas de salud, ubicación con mapa y consulta libre de turnos disponibles).
- Mostrar especialidades, médicos, consultorios y horarios disponibles sin exigir login previo.
- Evitar que un médico tenga dos turnos superpuestos.
- Evitar que un paciente reserve dos turnos activos con el mismo médico.
- Confirmar la llegada mediante un QR asociado a una reserva.
- Registrar estados del turno y hora real de check-in.
- Ordenar la sala de espera según la llegada.
- Permitir cancelaciones y liberar la disponibilidad.
- Mantener separados los permisos de visitante público, paciente autenticado y administrador de la clínica (`admin`).

## 6. Actores y permisos

| Actor | Responsabilidades | Acciones principales |
|---|---|---|
| Visitante (No logueado) | Informarse y explorar disponibilidad | Ver novedades, ofertas/campañas, ubicación y mapa; consultar especialidades, médicos activos y turnos disponibles (`GET /api/turnos/disponibles`); registrarse |
| Paciente (`rol = paciente`) | Gestionar sus propios turnos y perfil | Confirmar reserva de turno (`POST /api/turnos/reservar`), cancelar turno, ver su QR, ver sus turnos y editar su perfil |
| Administrador / Recepción (`rol = admin`) | Operar la atención del día y configurar el sistema | Escanear QR (`POST /api/turnos/checkin`), consultar sala de espera y marcar turno como atendido; realizar ABM de especialidades, médicos, consultorios, pacientes y creación de turnos disponibles en agenda (`POST /api/turnos`) |
| Sistema | Aplicar reglas automáticas | Validar disponibilidad, generar QR, actualizar estados en ventana de 15 minutos |

Un paciente no podrá modificar ni consultar información de otros pacientes. Las operaciones de recepción (check-in y sala de espera) y de administración (ABM sobre médicos, consultorios, especialidades y generación de turnos) se unifican bajo el rol `admin`.

## 7. Alcance

### Incluido

- **Portal público sin login:** secciones de Novedades, Ofertas/Campañas de salud, Ubicación y Mapa interactivo de la sede, y buscador público de especialidades, médicos y turnos disponibles.
- Catálogo y ABM de especialidades, médicos (con relación N:M a especialidades mediante tabla intermedia `medicos_especialidades`) y consultorios.
- Tabla unificada `usuarios` que integra datos personales (`dni`, `nombre`, `apellido`) y credenciales/rol (`email`, `password_hash`, `rol`, `activo`), diferenciando a los pacientes del personal de la clínica.
- Generación y consulta de turnos disponibles por médico y fecha.
- Reserva, cancelación y consulta de turnos propios.
- Generación de código QR por reserva y envío de confirmación con botón de cancelación.
- Check-in en recepción (ventana de 15 minutos), sala de espera y cambio a estado `atendido`.
- Estados de turno: `disponible`, `reservado`, `confirmado`, `atendido`, `cancelado`, `ausente`.
- Validación de roles y datos de entrada.

### Fuera de alcance para la primera versión

- Historia clínica y carga de diagnósticos.
- Facturación, pagos y obras sociales.
- Recetas electrónicas.
- Videoconsultas.
- Integración con sistemas externos de salud.
- Aplicación móvil nativa.
- Envío real de correo o SMS si no se dispone de un servicio de prueba; durante el desarrollo se podrá registrar o simular la notificación.

## 8. Requisitos funcionales

| ID | Requisito | Criterio de aceptación |
|---|---|---|
| RF-01 | Consultar especialidades | El sistema devuelve las especialidades activas ordenadas por nombre |
| RF-02 | Consultar médicos | Al seleccionar una especialidad se muestran sus médicos activos |
| RF-03 | Consultar disponibilidad | Para un médico y fecha se muestran únicamente franjas libres y válidas |
| RF-04 | Reservar turno | Una reserva válida cambia el estado a `reservado` y devuelve los datos de confirmación y QR |
| RF-05 | Cancelar turno | Una cancelación autorizada cambia el estado a `cancelado` y libera la franja |
| RF-06 | Validar QR | Un QR válido dentro de la ventana permitida registra hora de llegada y cambia el estado a `confirmado` |
| RF-07 | Marcar ausencia | Si no se realiza check-in hasta 15 minutos después del horario, el turno pasa a `ausente` |
| RF-08 | Consultar sala de espera | Recepción obtiene los pacientes confirmados ordenados por hora de llegada |
| RF-09 | Administrar catálogo | Administración puede crear, modificar y desactivar médicos, especialidades y consultorios |
| RF-10 | Consultar estadísticas | Administración visualiza ocupación, especialidades más solicitadas y porcentaje de ausentismo |

## 9. Requisitos no funcionales

- La API utilizará JSON y verbos HTTP coherentes.
- Las contraseñas no se almacenarán en texto plano.
- Las consultas SQL utilizarán parámetros, nunca concatenación de datos ingresados por usuarios.
- Los permisos se validarán en el backend; ocultar botones en el frontend no constituye autorización.
- Las fechas se almacenarán en un único campo `datetime` para el turno.
- Las respuestas de error tendrán un formato uniforme con código HTTP y mensaje.
- Las operaciones críticas deberán ser idempotentes o validar el estado actual antes de modificarlo.
- La interfaz deberá ser usable en computadora y teléfono, con etiquetas claras y estados distinguibles sin depender únicamente del color.

## 10. Reglas de negocio

1. Un turno corresponde a un único paciente, un médico y una fecha/hora.
2. Un médico no puede tener dos turnos activos superpuestos.
3. Un paciente no puede tener dos turnos activos con el mismo médico en la misma franja.
4. Solo se pueden reservar turnos futuros y pertenecientes a una agenda habilitada.
5. Un turno reservado puede cancelarse hasta el límite operativo definido por el centro.
6. El check-in se acepta desde 15 minutos antes hasta 15 minutos después del horario del turno.
7. Un QR no puede utilizarse dos veces.
8. Un turno cancelado o ausente no puede pasar a `atendido`.
9. La sala de espera se ordena por `hora_checkin`, no por el horario teórico del turno.
10. Los datos históricos de los turnos no se eliminan físicamente; se conserva su estado para estadísticas y auditoría.

## 11. Casos de uso prioritarios

### CU-01 - Consultar disponibilidad (Público) y Reservar un turno (Autenticado)

**Actor:** Visitante público / Paciente autenticado.  
**Precondiciones:** médico activo y franja disponible en estado `disponible`.  
**Flujo:** el visitante selecciona especialidad, médico y fecha sin necesidad de iniciar sesión (`GET /api/turnos/disponibles`); al elegir un horario para reservar, si no inició sesión el sistema le solicita ingresar o registrarse; luego ejecuta `POST /api/turnos/reservar`, pasa el turno a `reservado`, genera el QR y envía la confirmación por email con botón de cancelación.  
**Alternativas:** si otra persona ocupó la franja, se informa el conflicto y se solicita elegir otra.  
**Resultado:** turno `reservado`.

### CU-02 - Cancelar un turno

**Actor:** Paciente.  
**Precondiciones:** el turno pertenece al paciente y se encuentra `reservado`.  
**Flujo:** solicita la cancelación (`PATCH /api/turnos/{id}/cancelar`); el sistema cambia el estado a `cancelado` y libera la franja.  
**Resultado:** turno `cancelado`.

### CU-03 - Registrar llegada (Check-in) y Atención

**Actor:** Recepción.  
**Precondiciones:** existe un turno reservado y se presenta su QR.  
**Flujo:** recepción escanea el código (`POST /api/turnos/checkin`); el sistema valida la ventana de 15 minutos y registra `hora_checkin`. Luego aparece en `GET /api/turnos/sala-espera` y al ser llamado se marca con `PATCH /api/turnos/{id}/atender`.  
**Resultado:** turno `confirmado` (y posteriormente `atendido`) o `ausente` si no cumple la ventana.

## 12. Contrato de API RESTful

El listado completo y actualizado de endpoints por módulo (Público sin ingreso, Pacientes autenticados, Recepción y Backoffice/Administración) se encuentra detallado en [`alcance_y_endpoints.md`](./alcance_y_endpoints.md).

Puntos clave del contrato:
- **Consulta pública sin login:** `GET /api/especialidades`, `GET /api/medicos?especialidad={id}` y `GET /api/turnos/disponibles?medico={id}&fecha={fecha}` están abiertos a usuarios no autenticados.
- **Acciones de paciente autenticado:** `POST /api/turnos/reservar`, `PATCH /api/turnos/{id}/cancelar`, `GET /api/pacientes/{dni}`, `PATCH /api/pacientes/{dni}` y `GET /api/turnos?dni={dni}`.
- **Operación en Recepción:** `POST /api/turnos/checkin`, `GET /api/turnos/sala-espera` y `PATCH /api/turnos/{id}/atender`.
- **ABM en Backoffice:** alta, modificación y baja lógica (`/baja`) de especialidades, médicos, consultorios y pacientes, además de la apertura de turnos disponibles (`POST /api/turnos`) y filtros (`GET /api/turnos?medico={id}`, `GET /api/turnos?estado={estado}`).

## 13. Modelo conceptual mínimo

Entidades principales (ver diagrama ERD en [`diagramas.md`](./diagramas.md)):

- `usuarios`: **tabla unificada de usuarios y pacientes** (incluye `id`, `dni`, `nombre`, `apellido`, `email`, `password_hash`, `rol` y `activo`). El campo `rol` distingue únicamente entre `paciente` y `admin` (personal de la clínica que abarca recepción y administración).
- `especialidades`: catálogo de especialidades médicas (`id`, `nombre`).
- `medicos`: profesionales del centro (`id`, `nombre`, `apellido`, `matricula`, `id_consultorio`, `activo`).
- `medicos_especialidades`: **tabla intermedia (N:M)** que vincula médicos con especialidades (`id`, `id_medico`, `id_especialidad`). *(Nota: esquema extensible a `obras_sociales` si se opta por coberturas).*
- `consultorios`: espacios físicos de atención (`id`, `nombre`, `ubicacion`, `activo`).
- `turnos`: franjas horarias de 30 minutos (`id`, `id_usuario`, `id_medico`, `id_consultorio`, `fecha_hora` en un único campo `datetime`, `estado`, `qr_token`, `hora_checkin`).

### Ajustes aplicados a partir de la revisión en clase

1. **Unificación `usuarios` - `pacientes`:** Se eliminó la separación entre `usuarios`, `roles` y `pacientes`, consolidando todo en una única tabla `usuarios` con columna `rol`.
2. **Tabla intermedia N:M (`medicos_especialidades`):** Se incorporó la relación muchos a muchos entre médicos y especialidades (o equivalente con obras sociales).
3. **Consulta de turnos públicos sin ingreso:** El endpoint `GET /api/turnos/disponibles` pasó a ser público para que cualquier visitante consulte horarios antes de registrarse.
4. **Más vistas para usuario no logueado:** Se sumaron al alcance del portal público las secciones de **Novedades**, **Ofertas / Campañas de salud** y **Ubicación con Mapa interactivo**.

## 14. Riesgos y decisiones pendientes

| Riesgo o decisión | Impacto | Resolución propuesta |
|---|---|---|
| Uso de QR real o simulado | Medio | Generar un token firmado o aleatorio y documentar la simulación del envío |
| Servicio de correo no disponible | Medio | Separar generación de confirmación de envío y usar un adaptador de prueba |
| Doble reserva simultánea | Alto | Transacción SQL y revalidación de disponibilidad al confirmar |
| Ambigüedad sobre cancelaciones | Medio | Definir un límite configurable y mostrarlo al paciente |
| Datos de prueba insuficientes | Medio | Crear un dataset reproducible con especialidades, médicos, agendas y turnos |
| Regla de ausentismo | Alto | Mantener la tolerancia de 15 minutos como configuración documentada |

## 15. Entregables del Hito 1

- Descripción del problema y justificación de la solución.
- Objetivo general y objetivos específicos.
- Actores, permisos y alcance.
- Requisitos funcionales y no funcionales.
- Reglas de negocio.
- Casos de uso prioritarios.
- Modelo conceptual inicial y diagramas.
- Contrato preliminar de endpoints.
- Prototipo de baja fidelidad del portal del paciente y del backoffice.
- Riesgos y decisiones pendientes.

El prototipo debe validar el flujo, no el diseño visual final. Antes de programar conviene revisar con el equipo que los nombres de estados, roles, política de cancelación y ventana de check-in sean los definitivos.
