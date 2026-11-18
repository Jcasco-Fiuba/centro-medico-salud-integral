# Frontend

Aplicación server-side con Flask y plantillas Jinja (`http://127.0.0.1:5001` por
defecto). Esta estructura es la base compartida de `develop`; cada equipo agrega
sus pantallas dentro de su área.

## Estructura acordada

```text
frontend/
├── app.py
├── routes/                  # Blueprints Flask, separados por área
├── services/                # Llamadas server-side a la API y sesión
├── templates/
│   ├── base.html             # Plantilla madre: no duplicar por pantalla
│   ├── components/           # Macros Jinja reutilizables
│   ├── public/               # Portal y consulta pública (equipo Paciente)
│   ├── auth/                 # Inicio de sesión y registro
│   ├── paciente/             # Vistas autenticadas del paciente
│   ├── recepcion/            # Recepción y sala de espera
│   └── administracion/       # Backoffice administrativo
└── static/
    ├── css/
    │   ├── tokens.css         # Variables visuales compartidas
    │   ├── base.css           # Reset, tipografía y reglas globales
    │   ├── components.css     # Componentes compartidos
    │   └── pages/<área>/      # Estilos propios de cada área/pantalla
    ├── js/
    │   ├── base.js            # Interacciones globales y accesibles
    │   └── pages/<área>/      # JavaScript propio de cada pantalla
    └── img/                  # Imágenes e íconos
```

Las carpetas `static/css/pages/` y `static/js/pages/` se subdividen por las
mismas áreas: `public`, `auth`, `paciente`, `recepcion` y `administracion`.

## Responsables y límites

| Rama de trabajo | Rutas | Plantillas | CSS y JS |
| --- | --- | --- | --- |
| `feature/autenticacion` | `routes/auth.py` | `templates/auth/` | `static/css/pages/auth/`, `static/js/pages/auth/` |
| `feature/paciente-templates` | `routes/public.py`, `routes/paciente.py` | `templates/public/`, `templates/paciente/` | `static/css/pages/public/`, `static/css/pages/paciente/` y sus equivalentes en `js/` |
| `feature/recepcion` | `routes/recepcion.py` | `templates/recepcion/` | `static/css/pages/recepcion/`, `static/js/pages/recepcion/` |
| `feature/administracion` | `routes/administracion.py` | `templates/administracion/` | `static/css/pages/administracion/`, `static/js/pages/administracion/` |

El portal público pertenece al área Paciente para evitar que quede sin
responsable. `base.html`, `tokens.css`, `base.css`, `components.css` y
`base.js` son compartidos: no crear copias por equipo. Si una pantalla necesita
una regla propia, va en el CSS de su área; si un componente sirve a varias áreas,
se conversa antes de tocar los archivos compartidos.

### Convenciones de nombres

- Una plantilla por vista, en minúsculas y con guiones bajos: `login.html`,
  `registro.html`, `portal.html`.
- Un CSS/JS por pantalla o flujo, dentro de la carpeta del área y con el mismo
  nombre de la plantilla cuando corresponda.
- Las plantillas de pantalla extienden `base.html`; no repiten `<html>`, `<head>`
  ni las hojas globales.
- Cada plantilla carga su CSS en el bloque `page_css` y su JavaScript en
  `page_scripts`. Los archivos compartidos ya se cargan desde `base.html`.
- Los nombres de rutas, archivos y endpoints se acuerdan en español y se
  mantienen consistentes. No crear carpetas alternativas como `html/`, `css/`
  o `js/` en la raíz.
- Antes de agregar una vista, revisar si ya existe una con ese propósito y
  coordinar cambios compartidos para reducir conflictos al integrar ramas.

## Reglas de integración

- Partir de `develop` actualizado y trabajar en la rama del área correspondiente.
- No cambiar el nombre de los blueprints existentes ni registrar un blueprint
  por segunda vez; el registro central está en `routes/__init__.py`.
- La comunicación con el backend se hace únicamente desde Python con
  `requests`, a través de `services/api_client.py`. El JavaScript del navegador
  es para interacción visual: no usar `fetch`, Axios ni solicitudes equivalentes.
- Mantener la validación de permisos en el backend; ocultar controles no protege
  una ruta.
- No agregar dependencias sin acordarlo con el equipo.

## Inicio local (Frontend en puerto 5001, Backend en puerto 5000)

Desde la carpeta `frontend/`:

```bash
cd frontend
bash ./init.sh
```

O manualmente:

```bash
cd frontend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Configurar FRONTEND_SECRET_KEY (mínimo 32 caracteres) en frontend/.env
python app.py
```

Variables definidas en [`frontend/.env.example`](./.env.example):

- `FRONTEND_SECRET_KEY`: clave estable de al menos 32 caracteres para firmar el
  identificador de la cookie de sesión (por ejemplo generada con
  `python3 -c "import secrets; print(secrets.token_hex(32))"`).
- `FRONTEND_PORT`: puerto del servidor frontend (por defecto `5001`).
- `FRONTEND_COOKIE_SECURE`: `0` en desarrollo HTTP local; `1` bajo HTTPS.
- `FRONTEND_SESSION_TTL`: tiempo de vida de la sesión en segundos (por defecto
  `3600`).
- `FRONTEND_SESSION_DIR` (opcional): directorio donde se guardan los archivos de
  sesión server-side (por defecto `frontend/.flask_session/`).
- `API_URL`: URL base del backend (por defecto `http://127.0.0.1:5000`).
- `BACKEND_API_URL`: URL base de los endpoints REST (por defecto
  `http://127.0.0.1:5000/api`).

## Gestión de sesión server-side

Las sesiones del frontend se almacenan del lado del servidor mediante
`FileSystemSessionInterface` (`services/session_store.py`) en el directorio
configurado por `FRONTEND_SESSION_DIR` (por defecto `frontend/.flask_session/`,
con permisos `0700`/`0600`).

Al autenticarse mediante `guardar_sesion_autenticada()` (`services/api_client.py`):

- `session["id_usuario"]` almacena el `usuarios.id` entero devuelto por el
  backend (que coincide con la clave foránea `turnos.id_usuario`).
- `session["dni"]` almacena el DNI (`usuarios.dni`).
- `session["access_token"]` conserva el JWT firmado por el backend para enviarlo
  en `Authorization: Bearer <access_token>` desde Python (`requests`).
- `session["usuario"]` conserva los datos públicos del usuario autenticado
  (`id`, `id_usuario`, `dni`, `nombre`, `apellido`, `email`, `rol`) y
  `session["_expires_at"]` registra el instante de expiración.
- La cookie del navegador (`cmsi_session`) solo transporta el identificador
  aleatorio de sesión `sid` firmado (`HttpOnly`, `SameSite=Lax`, y `Secure`
  cuando `FRONTEND_COOKIE_SECURE=1`), que se regenera al iniciar sesión y se
  elimina junto con el archivo server-side en `POST /auth/logout` o ante un `401`
  del backend.
