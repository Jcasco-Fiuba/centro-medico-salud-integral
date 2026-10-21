# Diagramas del Sistema

## Esquema de Base de Datos (ERD)
Obligatorio: Se utiliza un único campo `datetime` para la fecha y hora del turno, y no campos separados.

```mermaid
erDiagram
    PACIENTES ||--o{ TURNOS : reserva
    MEDICOS ||--o{ AGENDAS : configura
    MEDICOS ||--o{ TURNOS : atiende

    PACIENTES {
        int id PK
        string nombre
        string email
        string password_hash
    }
    MEDICOS {
        int id PK
        string nombre
        string especialidad
        string consultorio_asignado
    }
    AGENDAS {
        int id PK
        int id_medico FK
        string dias_atencion
        time horario_inicio
        time horario_fin
        int duracion_turno_minutos
    }
    TURNOS {
        int id PK
        int id_paciente FK
        int id_medico FK
        datetime fecha_hora
        string estado "disponible, reservado, confirmado, atendido, cancelado, ausente"
    }
```

## Flujo de Reserva de Turnos

```mermaid
sequenceDiagram
    actor Paciente
    participant Frontend
    participant Backend
    participant BaseDatos as MySQL

    Paciente->>Frontend: Elige especialidad, médico, día y hora
    Frontend->>Backend: POST /api/turnos/reservar
    Backend->>BaseDatos: UPDATE turno (estado='reservado')
    Backend->>Backend: Genera código QR
    Backend-->>Paciente: Envía Email con confirmación y QR
```

## Flujo de Check-in en Recepción

```mermaid
flowchart TD
    A[Paciente llega a la clínica] --> B{Recepción escanea QR}
    B --> C{¿Está dentro de los 15 min de tolerancia?}
    C -- Sí --> D[Estado = 'Confirmado / En sala de espera']
    C -- No --> E[Estado = 'Ausente']
    D --> F[Registra hora de llegada real]
    E --> G[Penaliza y contabiliza en Dashboard de ausentismo]
```