# Diagramas del Sistema

## Esquema de Base de Datos (ERD)
Obligatorio: Se utiliza un único campo `datetime` para la fecha y hora del turno, y no campos separados.

```mermaid
erDiagram
    ROLES ||--o{ USUARIOS : asigna
    USUARIOS ||--o| PACIENTES : representa
    ESPECIALIDADES ||--o{ MEDICOS : clasifica
    CONSULTORIOS ||--o{ TURNOS : utiliza
    MEDICOS ||--o{ AGENDAS : configura
    MEDICOS ||--o{ TURNOS : atiende
    PACIENTES ||--o{ TURNOS : reserva

    ROLES {
        int id PK
        string nombre
    }
    USUARIOS {
        int id PK
        string email UK
        string password_hash
        int id_rol FK
        boolean activo
    }
    PACIENTES {
        int id PK
        int id_usuario FK
        string nombre
        string dni UK
    }
    ESPECIALIDADES {
        int id PK
        string nombre UK
    }
    MEDICOS {
        int id PK
        string nombre
        string matricula UK
        int id_especialidad FK
    }
    CONSULTORIOS {
        int id PK
        string nombre
        string ubicacion
    }
    AGENDAS {
        int id PK
        int id_medico FK
        string dia_semana
        time horario_inicio
        time horario_fin
        int duracion_turno_minutos
    }
    TURNOS {
        int id PK
        int id_paciente FK
        int id_medico FK
        int id_consultorio FK
        datetime fecha_hora
        string estado
        string qr_token UK
        datetime hora_checkin
    }
```

Los valores posibles de `TURNOS.estado` son `disponible`, `reservado`, `confirmado`,
`atendido`, `cancelado` y `ausente`. La disponibilidad puede calcularse a partir de
`AGENDAS` y de los turnos existentes; no es necesario persistir una fila por cada
franja libre.

## Flujo de Reserva de Turnos

```mermaid
sequenceDiagram
    actor Paciente
    participant Frontend
    participant Backend
    participant BaseDatos as MySQL

    Paciente->>Frontend: Elige especialidad, médico, día y hora
    Frontend->>Backend: POST /api/turnos
    Backend->>BaseDatos: Transacción: valida y crea reserva
    Backend->>Backend: Genera código QR
    Backend-->>Paciente: Envía Email con confirmación y QR
```

## Flujo de Check-in en Recepción

```mermaid
flowchart TD
    A[Paciente llega a la clínica] --> B{Recepción escanea QR}
    B --> C{¿Está dentro de la ventana -15/+15 min?}
    C -- Sí --> D[Estado = 'Confirmado / En sala de espera']
    C -- No --> E[Estado = 'Ausente']
    D --> F[Registra hora de llegada real]
    E --> G[Penaliza y contabiliza en Dashboard de ausentismo]
```