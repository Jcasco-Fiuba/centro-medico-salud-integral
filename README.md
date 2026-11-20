# Centro Médico Salud Integral

Sistema web de gestión de turnos médicos con check-in por código QR. Proyecto
integrador de **Introducción al Desarrollo de Software** (TB022, FIUBA,
cátedra Lanzillotta), 2do cuatrimestre 2026.

El sistema permite a los pacientes consultar la cartilla y los turnos
disponibles, reservar y cancelar turnos, y presentar un código QR en recepción
para registrar su llegada. El personal administrativo gestiona médicos,
especialidades, consultorios y agendas, y atiende la sala de espera.

## Integrantes

**Grupo 18 - Seguidores del Loro Matteoli & larp**

| Integrante | Padrón |
| --- | --- |
| Jorge David Casco Coronel | 116199 |
| Josefina Abril Najar Gacek | 113354 |
| Alan Nieves Villagra | 113133 |
| Jorge Bencomo Navas | 116303 |
| Federico Nahuel Gioda | 116480 |
| Valentina Nieto | 109046 |
| Nicolás Galizio | 116617 |
| Cristopher Silva | 116121 |
| Lorenzo Decillo | 116418 |

## Arquitectura

El proyecto está dividido en dos aplicaciones Flask independientes y una base
de datos MySQL:

```text
Navegador ──► Frontend (Flask + Jinja, puerto 5001)
                 │  requests (Python, server-side)
                 ▼
              Backend / API REST (Flask, puerto 5000) ──► MySQL (centro_medico)
```

- **Frontend:** renderiza las páginas en el servidor con plantillas Jinja. Toda
  la comunicación con la API se hace desde Python con `requests`, a través de
  `frontend/services/api_client.py`. El JavaScript del navegador se usa solo
  para interacción visual.
- **Backend:** API REST con respuestas en JSON. Las consultas a MySQL se
  escriben con SQL explícito y parámetros enlazados mediante MySQL
  Connector/Python; el proyecto no usa ORM.
- **Autenticación:** el backend emite un JWT (`HS256`) al iniciar sesión. El
  frontend lo guarda en una sesión server-side y lo envía en
  `Authorization: Bearer <token>`.

## Estructura del repositorio

```text
centro-medico-salud-integral/
├── backend/
│   ├── app.py
│   ├── init.sh               # Crea el entorno, instala dependencias e inicia la API
│   ├── app/
│   │   ├── routes/           # Endpoints (blueprints) por entidad
│   │   ├── services/         # Reglas de negocio
│   │   ├── repository/       # Consultas SQL explícitas
│   │   └── validators/       # Validación de los datos recibidos
│   └── db/
│       ├── db.sql            # Creación de tablas y datos iniciales
│       └── crear_admin_prueba.py
├── frontend/
│   ├── app.py
│   ├── init.sh
│   ├── routes/               # Blueprints por área (public, auth, paciente, recepcion, administracion)
│   ├── services/             # Cliente de la API y sesión
│   ├── templates/            # Plantillas Jinja por área y components/ reutilizables
│   └── static/               # CSS por área, JS de interfaz e imágenes
└── docs/                     # Plan del Hito 1, alcance, endpoints, diagramas e informe
```

Cada carpeta tiene su propio README con más detalle:

- [`backend/README.md`](./backend/README.md): configuración de la API, base de
  datos de prueba y consultas SQL.
- [`backend/db/README.md`](./backend/db/README.md): esquema y datos iniciales.
- [`frontend/README.md`](./frontend/README.md): estructura de plantillas,
  convenciones de nombres y sesión server-side.

## Funcionalidades

### Portal público (sin iniciar sesión)

- Inicio con novedades, campañas de salud, horarios y ubicación con mapa.
- Cartilla de especialidades y profesionales.
- Consulta de turnos disponibles por médico y fecha. El inicio de sesión se
  pide recién al confirmar la reserva.
- Registro de pacientes e inicio de sesión.

### Paciente

- Reserva de turnos en 4 pasos: especialidad → profesional → fecha y hora →
  confirmación.
- Mis turnos: listado con estados, detalle con el código QR y comprobante
  descargable.
- Cancelación de turnos con al menos 24 horas de anticipación.
- Mi perfil: consulta y edición de nombre, apellido y email.

### Recepción y administración (rol `admin`)

- Check-in con el código QR del turno, dentro de la ventana de 15 minutos antes
  o después del horario.
- Sala de espera con los pacientes confirmados del día y marcado como atendido.
- ABM de médicos, especialidades y consultorios.
- Agendas, consulta de disponibilidad y alta de turnos.
- Dashboard con indicadores de ocupación y ausentismo.

### Reglas de negocio

- Todos los turnos duran 30 minutos y hay una sola sede.
- Un médico no puede tener turnos superpuestos.
- Un paciente no puede tener dos turnos activos (futuros, `reservado` o
  `confirmado`) con el mismo médico.
- Estados del turno: `disponible`, `reservado`, `confirmado`, `atendido`,
  `cancelado` y `ausente`. Si el paciente intenta el check-in más de 15 minutos
  tarde, el turno queda `ausente`.

## Requisitos

- Python 3
- MySQL 8.x (o MariaDB) en `localhost:3306`
- Bash (Linux, macOS o WSL en Windows)

## Puesta en marcha local

Los comandos se ejecutan desde la raíz del repositorio. Se necesitan **dos
terminales**: una para el backend y otra para el frontend.

### 1. Base de datos

Con el servicio de MySQL iniciado (`sudo systemctl start mysql` en Ubuntu),
cargá el esquema y los datos iniciales:

```bash
mysql -u root -p < backend/db/db.sql
```

> **Importante:** `db.sql` crea la base `centro_medico` y vuelve a crear sus
> tablas. No lo ejecutes contra una base con datos que quieras conservar. Para
> trabajar con una instancia o un schema separado, seguí las opciones del
> [`backend/README.md`](./backend/README.md).

### 2. Backend (terminal 1, puerto 5000)

```bash
cd backend
./init.sh
```

La primera ejecución crea el entorno virtual `.venv`, instala las dependencias
y copia `.env.example` a `.env`. Completá en `backend/.env`:

- `DB_HOST=127.0.0.1`, `DB_PORT=3306`, `DB_NAME=centro_medico`, `DB_USER` y
  `DB_PASSWORD` con los datos de tu MySQL.
- `JWT_SECRET_KEY` con una clave de al menos 32 caracteres:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Volvé a ejecutar `./init.sh`. La API queda en `http://127.0.0.1:5000` y se
puede verificar en `http://127.0.0.1:5000/api/especialidades`. La raíz `/`
responde `404` porque la API no tiene página de inicio.

### 3. Frontend (terminal 2, puerto 5001)

```bash
cd frontend
./init.sh
```

Completá `FRONTEND_SECRET_KEY` en `frontend/.env` (se genera con el mismo
comando que `JWT_SECRET_KEY`) y volvé a ejecutar `./init.sh`. El sitio queda en
**http://127.0.0.1:5001**.

Para detener cualquiera de los dos servidores, usá `Ctrl + C` en su terminal.

### 4. Cuenta de administrador

`db.sql` no incluye una cuenta `admin` con clave fija. Para crearla en la base
local de desarrollo:

```bash
cd backend
ADMIN_TEST_PASSWORD="<clave_de_al_menos_8_caracteres>" \
./.venv/bin/python db/crear_admin_prueba.py --confirmar-base-desarrollo-local
```

El script crea `admin@saludintegral.com` (DNI `11222333`) y toma la conexión de
`backend/.env`. Si la cuenta ya existe, no modifica nada.

## Cuentas de prueba

| Rol | Email | Contraseña |
| --- | --- | --- |
| Paciente | `marta@gomez.com` | `12345678` |
| Paciente | `juan@perez.com` | `juan5555` |
| Admin | `admin@saludintegral.com` | la definida en `ADMIN_TEST_PASSWORD` |

Los turnos de `db.sql` tienen fechas fijas. Para probar una reserva se necesitan
turnos con fecha futura, que se pueden crear desde **Administración → Agendas**
o con un `INSERT` en la tabla `turnos`.

## Endpoints de la API

Todos los endpoints tienen el prefijo `/api` y responden en JSON. Los marcados
como públicos no requieren token. El resto exige
`Authorization: Bearer <token>` y el rol indicado.

| Método | Endpoint | Acceso |
| --- | --- | --- |
| `POST` | `/api/auth/login` | Público |
| `GET` | `/api/auth/me` | Usuario autenticado |
| `POST` | `/api/pacientes` | Público (registro) |
| `GET` | `/api/pacientes` | `admin` |
| `GET` / `PATCH` | `/api/pacientes/<dni>` | El propio paciente o `admin` |
| `PATCH` | `/api/pacientes/<dni>/baja` | `admin` |
| `GET` | `/api/especialidades`, `/api/especialidades/<id>` | Público |
| `POST` | `/api/especialidades` | `admin` |
| `PATCH` | `/api/especialidades/<id>` | `admin` |
| `GET` | `/api/medicos?especialidad=<id>`, `/api/medicos/<id>` | Público |
| `POST` | `/api/medicos` | `admin` |
| `PATCH` | `/api/medicos/<id>`, `/api/medicos/<id>/baja` | `admin` |
| `GET` | `/api/consultorios`, `/api/consultorios/<id>` | Público |
| `POST` | `/api/consultorios` | `admin` |
| `PATCH` | `/api/consultorios/<id>`, `/api/consultorios/<id>/baja` | `admin` |
| `GET` | `/api/turnos/disponibles?medico=<id>&fecha=<AAAA-MM-DD>` | Público |
| `GET` | `/api/turnos` | Paciente (solo los propios) o `admin` |
| `GET` | `/api/turnos/<id>` | El paciente titular o `admin` |
| `POST` | `/api/turnos` | `admin` |
| `POST` | `/api/turnos/reservar` | Paciente |
| `PATCH` | `/api/turnos/<id>/cancelar` | El paciente titular o `admin` |
| `POST` | `/api/turnos/checkin` | `admin` |
| `GET` | `/api/turnos/sala-espera` | `admin` |
| `PATCH` | `/api/turnos/<id>/atender` | `admin` |

El detalle de cada endpoint, con sus parámetros y códigos de respuesta, está en
[`docs/alcance_y_endpoints.md`](./docs/alcance_y_endpoints.md).

## Base de datos

El script [`backend/db/db.sql`](./backend/db/db.sql) crea seis tablas:

- `usuarios`: pacientes y administradores (rol `paciente` o `admin`).
- `especialidades`
- `consultorios`
- `medicos`
- `medicos_especialidades`: relación N:M entre médicos y especialidades.
- `turnos`: fecha y hora en un único campo `DATETIME`, estado y código del QR.

El diagrama entidad-relación está en [`docs/diagramas.md`](./docs/diagramas.md).

## Restricciones de la cátedra

- Sin ORM: todas las consultas se escriben en SQL explícito.
- Sin `fetch`, Axios, `XMLHttpRequest` ni equivalentes en el navegador: el
  frontend se comunica con la API únicamente desde Python con `requests`.
- Endpoints con el verbo HTTP correcto, datos en JSON y seguridad en todas las
  rutas privadas.
- Fecha y hora en un único campo `DATETIME`.
- Diseño responsive.
- Sin variables globales, sin ciclos infinitos, sin código repetido y con código
  modularizado.

## Flujo de trabajo con Git

- `main`: versiones entregadas.
- `develop`: rama de integración. Todo cambio nuevo parte de `develop`
  actualizado.
- `feature/<área>`: ramas de trabajo por funcionalidad, que se integran a
  `develop` mediante pull request.
- Los mensajes de commit siguen el formato `tipo(área): descripción`, por
  ejemplo `feat(paciente): agregar pantalla de perfil` o
  `fix(turnos): corregir validación de fecha`.
- Los archivos `.env` no se suben al repositorio; cada integrante usa su copia
  local a partir de `.env.example`.

## Documentación

- [`docs/hito1_plan.md`](./docs/hito1_plan.md): requisitos, reglas de negocio,
  casos de uso y riesgos.
- [`docs/alcance_y_endpoints.md`](./docs/alcance_y_endpoints.md): hipótesis,
  restricciones técnicas y contrato de la API.
- [`docs/diagramas.md`](./docs/diagramas.md): diagrama entidad-relación.
- [`docs/informe_final.md`](./docs/informe_final.md): informe del proyecto.
