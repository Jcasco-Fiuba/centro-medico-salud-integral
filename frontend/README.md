# Frontend

Aplicación server-side con Flask y plantillas Jinja. Esta estructura es la base
compartida de `develop`; cada equipo agrega sus pantallas dentro de su área.

## Estructura acordada

```text
frontend/
├── app.py
├── routes/                  # Blueprints Flask, separados por área
├── services/                # Llamadas server-side a la API
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
| `feature/auth` | `routes/auth.py` | `templates/auth/` | `static/css/pages/auth/`, `static/js/pages/auth/` |
| `feature/paciente` | `routes/public.py`, `routes/paciente.py` | `templates/public/`, `templates/paciente/` | `static/css/pages/public/`, `static/css/pages/paciente/` y sus equivalentes en `js/` |
| `feature/recepcion` | `routes/recepcion.py` | `templates/recepcion/` | `static/css/pages/recepcion/`, `static/js/pages/recepcion/` |
| `feature/administracion` | `routes/administracion.py` | `templates/administracion/` | `static/css/pages/administracion/`, `static/js/pages/administracion/` |

El portal público pertenece al área Paciente para evitar que quede sin
responsable. `base.html`, `tokens.css`, `base.css`, `components.css` y
`base.js` son compartidos: no crear copias por equipo. Si una pantalla necesita
una regla propia, va en el CSS de su área; si un componente sirve a varias áreas,
se conversa antes de tocar los archivos compartidos.

### Convenciones de nombres

- Una plantilla por vista, en minúsculas y con guiones bajos: `login.html`,
  `registro.html`, `mis_turnos.html`.
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

Ejemplo de una pantalla nueva:

```jinja
{% extends "base.html" %}

{% block title %}Iniciar sesión | Centro Médico{% endblock %}

{% block page_css %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/pages/auth/login.css') }}">
{% endblock %}

{% block body %}
  <main class="container">
    <!-- Contenido de esta pantalla -->
  </main>
{% endblock %}

{% block page_scripts %}
  <script src="{{ url_for('static', filename='js/pages/auth/login.js') }}" defer></script>
{% endblock %}
```

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

## Inicio local

Desde esta carpeta, instalar `requirements.txt` y ejecutar:

```bash
python app.py
```

La interfaz frontend queda disponible en `http://127.0.0.1:5001`; el backend
usa por defecto el puerto `5000`. El puerto del frontend se puede cambiar con la
variable `FRONTEND_PORT`.

Las plantillas Jinja no se abren directamente desde el explorador de archivos.
Hay que acceder a ellas a través de Flask para que se procesen los bloques y las
expresiones `{{ ... }}`.
