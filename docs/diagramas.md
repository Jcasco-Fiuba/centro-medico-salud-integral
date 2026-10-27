# Diagramas del Sistema

## Esquema de Base de Datos (ERD)
Obligatorio: Se utiliza un único campo `datetime` para la fecha y hora del turno, y no campos separados.

### Decisiones de Diseño en el Modelo de Datos:
1. **Unificación de Usuarios y Pacientes en `USUARIOS`:** Se unifican los datos de cuenta/autenticación (`email`, `password_hash`, `rol`) y los datos personales (`dni`, `nombre`, `apellido`, `activo`) en una única tabla `USUARIOS`. Mediante el campo `rol` se distingue únicamente entre `paciente` y `admin` (personal de la clínica que opera tanto recepción/check-in como la administración y ABMs).
2. **Tabla intermedia `MEDICOS_ESPECIALIDADES` (Relación N:M):** Se agrega la tabla intermedia entre `MEDICOS` y `ESPECIALIDADES` para permitir que un médico atienda una o más especialidades y una especialidad cuente con múltiples médicos (estructura equivalente si se vincula con `OBRAS_SOCIALES`).

```mermaid
erDiagram
    USUARIOS ||--o{ TURNOS : reserva
    MEDICOS ||--o{ MEDICOS_ESPECIALIDADES : posee
    ESPECIALIDADES ||--o{ MEDICOS_ESPECIALIDADES : agrupa
    CONSULTORIOS ||--o{ MEDICOS : asignado_a
    CONSULTORIOS ||--o{ TURNOS : utiliza
    MEDICOS ||--o{ TURNOS : atiende

    USUARIOS {
        int id PK
        string dni UK
        string nombre
        string apellido
        string email UK
        string password_hash
        string rol "paciente | admin"
        boolean activo
    }
    ESPECIALIDADES {
        int id PK
        string nombre UK
    }
    MEDICOS_ESPECIALIDADES {
        int id PK
        int id_medico FK
        int id_especialidad FK
    }
    CONSULTORIOS {
        int id PK
        string nombre
        string ubicacion
        boolean activo
    }
    MEDICOS {
        int id PK
        string nombre
        string apellido
        string matricula UK
        int id_consultorio FK
        boolean activo
    }
    TURNOS {
        int id PK
        int id_usuario FK "NULL mientras estado = disponible"
        int id_medico FK
        int id_consultorio FK
        datetime fecha_hora
        string estado "disponible | reservado | confirmado | atendido | cancelado | ausente"
        string qr_token UK
        datetime hora_checkin
    }
```

> **Alternativa / Extensión con Obras Sociales:** Si el equipo decide que la tabla intermedia adicional sea por Coberturas Médicas (`OBRAS_SOCIALES`), se mantiene el mismo patrón relacional mediante `OBRAS_SOCIALES (id PK, nombre UK, activo)` y la tabla intermedia `MEDICOS_OBRAS_SOCIALES (id PK, id_medico FK, id_obra_social FK)`.

Los valores posibles de `TURNOS.estado` son `disponible`, `reservado`, `confirmado`,
`atendido`, `cancelado` y `ausente`. Administración genera las franjas en estado `disponible` mediante `POST /api/turnos` y los usuarios pueden consultarlas públicamente sin iniciar sesión mediante `GET /api/turnos/disponibles`.

## Flujo de Consulta Pública y Reserva de Turnos

```mermaid
sequenceDiagram
    actor Visitante as Usuario (Sin Login / Logueado)
    participant Frontend
    participant Backend
    participant BaseDatos as MySQL

    Note over Visitante,Backend: 1. Navegación Pública (Sin necesidad de Login)
    Visitante->>Frontend: Explora inicio (Novedades, Ofertas, Ubicación/Mapa)
    Visitante->>Frontend: Consulta Especialidades, Médicos y Turnos Disponibles
    Frontend->>Backend: GET /api/especialidades
    Frontend->>Backend: GET /api/medicos?especialidad={id}
    Frontend->>Backend: GET /api/turnos/disponibles?medico={id}&fecha={fecha}
    Backend->>BaseDatos: SELECT turnos WHERE estado = 'disponible'
    BaseDatos-->>Backend: Listado de horarios disponibles
    Backend-->>Frontend: JSON con turnos disponibles

    Note over Visitante,Backend: 2. Reserva de Turno (Requiere Login / Registro)
    Visitante->>Frontend: Selecciona turno y confirma reserva (Inicia sesión si no lo hizo)
    Frontend->>Backend: POST /api/turnos/reservar
    Backend->>BaseDatos: UPDATE turnos SET id_paciente, estado='reservado', qr_token
    Backend->>Backend: Genera código QR
    Backend-->>Visitante: Envía Email con confirmación, QR y botón cancelar
```

## Flujo de Check-in en Recepción

```mermaid
flowchart TD
    A["Paciente llega a la clínica"] --> B{"Recepción escanea QR (POST /api/turnos/checkin)"}
    B --> C{"¿Está dentro de la ventana -15/+15 min?"}
    C -- Sí --> D["Estado = 'confirmado' (En sala de espera)"]
    C -- No --> E["Estado = 'ausente'"]
    D --> F["Registra hora_checkin y aparece en GET /api/turnos/sala-espera"]
    F --> G["Médico llama al paciente -> PATCH /api/turnos/{id}/atender -> Estado = 'atendido'"]
    E --> H["Contabiliza en métricas de ausentismo"]
```