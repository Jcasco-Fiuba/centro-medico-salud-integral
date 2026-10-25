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

Desarrollar una plataforma web con dos áreas:

1. **Portal de pacientes:** consulta de especialidades y profesionales, búsqueda de disponibilidad, reserva o cancelación de turnos y recepción de una confirmación con código QR.
2. **Backoffice de recepción/administración:** gestión de pacientes, médicos, especialidades, consultorios y agendas; escaneo o carga del QR; consulta de la sala de espera y visualización de estadísticas.

La solución estará compuesta por un frontend server-side, un backend REST en Flask y una base MySQL. La comunicación frontend-backend se realizará desde Python mediante `requests`, de acuerdo con las restricciones de la cátedra. Las consultas a MySQL se escribirán con SQL explícito, sin ORM.

## 4. Objetivo general

Centralizar la gestión de turnos del centro médico para que los pacientes puedan reservarlos de forma clara y el personal pueda controlar la llegada, la atención y el uso de los recursos.

## 5. Objetivos específicos

- Mostrar especialidades, médicos, consultorios y horarios disponibles.
- Evitar que un médico tenga dos turnos superpuestos.
- Evitar que un paciente reserve dos turnos activos con el mismo médico.
- Confirmar la llegada mediante un QR asociado a una reserva.
- Registrar estados del turno y hora real de check-in.
- Ordenar la sala de espera según la llegada.
- Permitir cancelaciones y liberar la disponibilidad.
- Obtener métricas de ocupación, demanda y ausentismo.
- Mantener separados los permisos de paciente, recepción y administración.

## 6. Actores y permisos

| Actor | Responsabilidades | Acciones principales |
|---|---|---|
| Paciente | Gestionar sus propios turnos | Consultar disponibilidad, reservar, cancelar, ver su QR y sus turnos |
| Recepción | Operar la atención del día | Consultar agenda, validar QR, registrar llegada, consultar sala de espera |
| Administrador | Configurar el sistema | Alta, modificación y baja lógica de pacientes, médicos, especialidades, consultorios y agendas; consultar estadísticas |
| Sistema | Aplicar reglas automáticas | Validar disponibilidad, generar QR, actualizar estados y calcular indicadores |

Un paciente no podrá modificar información de otros pacientes. Las operaciones de gestión sobre médicos, consultorios, especialidades y agendas quedarán restringidas a administración.

## 7. Alcance

### Incluido

- Catálogo de especialidades, médicos y consultorios.
- Configuración de agendas y duración de turnos.
- Consulta de disponibilidad por médico y fecha.
- Reserva, cancelación y consulta de turnos.
- Generación de un identificador QR por reserva.
- Check-in en recepción y sala de espera.
- Estados de turno: `disponible`, `reservado`, `confirmado`, `atendido`, `cancelado`, `ausente`.
- Dashboard básico con ocupación, demanda y ausentismo.
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

### CU-01 - Reservar un turno

**Actor:** Paciente.  
**Precondiciones:** paciente autenticado, médico activo y franja disponible.  
**Flujo:** selecciona especialidad, médico, fecha y hora; el sistema vuelve a validar disponibilidad; crea la reserva; genera QR y muestra la confirmación.  
**Alternativas:** si otra persona ocupó la franja, se informa el conflicto y se solicita elegir otra.  
**Resultado:** turno `reservado`.

### CU-02 - Cancelar un turno

**Actor:** Paciente.  
**Precondiciones:** el turno pertenece al paciente y se encuentra `reservado`.  
**Flujo:** solicita la cancelación; el sistema valida la política; cambia el estado y libera la franja.  
**Resultado:** turno `cancelado`.

### CU-03 - Registrar llegada

**Actor:** Recepción.  
**Precondiciones:** existe un turno reservado y se presenta su QR.  
**Flujo:** recepción escanea o ingresa el código; el sistema valida autenticidad, vigencia y ventana temporal; registra `hora_checkin`.  
**Resultado:** turno `confirmado` o `ausente` si no cumple la ventana.

### CU-04 - Consultar indicadores

**Actor:** Administrador.  
**Precondiciones:** existen turnos registrados y el usuario tiene permisos administrativos.  
**Flujo:** selecciona el período; el sistema agrupa los turnos por estado, especialidad y médico.  
**Resultado:** dashboard con métricas y período consultado.

## 12. Propuesta inicial de API

La API debe mantener nombres consistentes y separar recursos de acciones:

| Método | Endpoint | Acceso | Propósito |
|---|---|---|---|
| GET | `/api/especialidades` | Público/autenticado | Listar especialidades |
| GET | `/api/medicos?especialidad_id={id}` | Público/autenticado | Listar médicos |
| GET | `/api/consultorios` | Recepción/admin | Listar consultorios |
| GET | `/api/turnos/disponibles?medico_id={id}&fecha={YYYY-MM-DD}` | Paciente | Consultar franjas |
| POST | `/api/turnos` | Paciente | Crear reserva |
| GET | `/api/turnos/mis-turnos` | Paciente | Consultar turnos propios |
| PATCH | `/api/turnos/{id}/cancelacion` | Paciente/recepción | Cancelar un turno |
| POST | `/api/checkins` | Recepción | Validar QR y registrar llegada |
| GET | `/api/recepcion/sala-espera?fecha={YYYY-MM-DD}` | Recepción | Consultar sala de espera |
| GET | `/api/admin/estadisticas?desde={fecha}&hasta={fecha}` | Admin | Obtener indicadores |

Las rutas para alta, modificación y desactivación de catálogos deberán quedar bajo `/api/admin/...`. El nombre del recurso debe ser plural y los identificadores deben ser estables; no se recomienda usar el nombre del médico o el DNI como parte de la ruta.

### Compatibilidad con el acuerdo inicial del equipo

En las primeras conversaciones del equipo se propusieron rutas como `/pacientes/<dni>`,
`/medicos/<nombre>`, `/consultorios/<numero>` y filtros de turnos por médico o estado.
La idea funcional es válida, pero conviene ajustar la forma antes de implementarla:

- usar identificadores (`id`) en vez de nombres, porque los nombres pueden repetirse o cambiar;
- mantener los recursos en plural;
- usar `PATCH` para cambios parciales y `POST` para altas o acciones que crean un recurso;
- no usar un estado como si fuera un identificador de turno;
- declarar explícitamente el rol requerido para cada operación;
- preservar los datos personales del paciente fuera de URLs cuando no sea necesario.

Si la cátedra o el equipo exige conservar exactamente las rutas iniciales, este es el
contrato equivalente que debe documentarse:

| Método | Ruta acordada | Acceso | Observación |
|---|---|---|---|
| GET | `/pacientes` | Recepción/admin | Listar pacientes |
| GET | `/pacientes/{dni}` | Paciente/recepción/admin | Consultar un paciente; validar permisos |
| POST/PATCH | `/pacientes` o `/pacientes/{dni}` | Paciente | Crear o modificar el propio perfil |
| GET | `/medicos` | Público/autenticado | Listar médicos |
| GET | `/medicos/{id}` | Público/autenticado | Consultar un médico por ID |
| POST/PATCH | `/medicos` o `/medicos/{id}` | Admin | Alta o modificación |
| GET | `/consultorios` | Recepción/admin | Listar consultorios |
| GET | `/consultorios/{id}` | Recepción/admin | Consultar consultorio por ID |
| POST/PATCH | `/consultorios` o `/consultorios/{id}` | Admin | Alta o modificación |
| GET | `/especialidades` | Público/autenticado | Listar especialidades |
| POST/PATCH | `/especialidades` o `/especialidades/{id}` | Admin | Alta o modificación |
| GET | `/turnos` | Paciente/recepción/admin | Listar según rol y filtros |
| GET | `/turnos/{id}` | Paciente/recepción/admin | Consultar un turno |
| POST | `/turnos` | Paciente | Reservar un turno |
| PATCH | `/turnos/{id}` | Paciente/recepción/admin | Cambiar estado o datos permitidos |
| GET | `/turnos?medico_id={id}` | Recepción/admin | Filtrar por médico |
| GET | `/turnos?estado={estado}` | Recepción/admin | Filtrar por estado |

Las rutas `/turnos/{dni}`, `/turnos/{medico}`, `/turnos/{atendido}` y
`/turnos/{cancelado}` no deben implementarse literalmente: son ambiguas porque el
servidor no puede distinguir si el valor es un DNI, un nombre o un estado. Se reemplazan
por `/turnos?paciente_dni={dni}`, `/turnos?medico_id={id}` y
`/turnos?estado=atendido|cancelado`.

## 13. Modelo conceptual mínimo

Entidades principales:

- `pacientes`
- `roles`
- `usuarios`
- `especialidades`
- `medicos`
- `consultorios`
- `agendas`
- `turnos`

`usuarios` concentra autenticación y roles; `pacientes` contiene el perfil específico del paciente. `turnos` relaciona paciente, médico y fecha/hora, y conserva el estado y la hora de check-in. `agendas` define cuándo puede atender cada médico y la duración de cada franja. `especialidades` y `consultorios` deben ser entidades separadas para evitar duplicación y permitir cambios de catálogo.

### Revisión del esquema compartido por el equipo

Las entidades propuestas por el equipo son correctas como punto de partida:
`Pacientes`, `Médicos`, `Consultorios`, `Turnos` y `Especialidades`. Para que el
modelo soporte autenticación y permisos, se agregan `Usuarios` y `Roles`.

Cambios recomendados respecto de la planilla:

- `DNI` debe ser un dato único del paciente, pero no conviene usarlo como clave
  primaria de todas las relaciones; se recomienda un `id` interno y una restricción
  `UNIQUE` para DNI.
- `Médicos` necesita una relación con `Especialidades` y, preferentemente, una
  matrícula única.
- `Consultorios` debe tener un `id` interno y un nombre o número único.
- `Turnos` necesita fecha y hora, paciente, médico, consultorio y estado. También
  necesita `qr_token` y `hora_checkin` para cumplir el flujo definido.
- `Activo` es útil para baja lógica, pero no reemplaza el estado de un turno.
- La disponibilidad no debe guardarse como una lista fija de turnos disponibles:
  debe calcularse a partir de la agenda del médico y los turnos ya reservados.

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
