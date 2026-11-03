# Frontend

Frontend server-side con Flask y plantillas Jinja. Las vistas se organizan por
módulo para que cada división del equipo trabaje en su área y comparta la base
visual del sitio.

## Estructura

- `routes/`: rutas Flask separadas por área.
- `services/`: comunicación del servidor frontend con la API.
- `templates/`: plantilla base, componentes y pantallas Jinja por área.
- `static/css/`: tokens, estilos base, componentes y estilos específicos.
- `static/js/`: interacciones visuales del navegador.
- `static/img/`: imágenes e íconos del frontend.

La comunicación con la API debe hacerse desde Python con `requests`, según las
restricciones del proyecto. El JavaScript del navegador queda para interacciones
de interfaz; no debe realizar solicitudes a la API.

## Áreas de trabajo

- `auth/`: inicio de sesión y registro.
- `paciente/`: portal público y flujos de paciente.
- `recepcion/`: recepción y sala de espera.
- `administracion/`: backoffice administrativo.

Las rutas públicas están separadas en `routes/public.py` porque el visitante
puede explorar información y disponibilidad antes de autenticarse.

## Inicio local

Desde esta carpeta, instalar las dependencias de `requirements.txt` y ejecutar:

```bash
python app.py
```
