"""Cliente server-side para comunicarse con la API usando requests y gestión de sesión."""

import os
import time
from typing import Any

from flask import has_request_context, session
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:5000").rstrip("/")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", f"{API_URL}/api").rstrip("/")
TIMEOUT = int(os.getenv("BACKEND_REQUEST_TIMEOUT", "10"))
REQUEST_TIMEOUT = TIMEOUT


def guardar_sesion_autenticada(
    access_token: str,
    expires_in: int,
    usuario: dict[str, Any],
) -> None:
    """Guarda en la sesión server-side los datos del usuario autenticado y su JWT.

    Regenera el identificador de sesión para prevenir fijación de sesión y
    conserva las claves `session["id_usuario"]` (que corresponde a `usuarios.id`
    y coincide con la FK `turnos.id_usuario`) y `session["dni"]` requeridas
    por las vistas de `frontend/routes/paciente.py`. Como `session` usa
    `FileSystemSessionInterface`, ni el JWT ni el DNI viajan en la cookie del
    navegador (la cookie solo contiene el identificador aleatorio firmado).
    """
    id_usuario_raw = usuario.get("id_usuario", usuario.get("id"))
    dni_raw = usuario.get("dni")
    if id_usuario_raw is None or not dni_raw:
        raise ValueError("La respuesta de autenticación no incluye id_usuario o dni.")

    id_usuario = int(id_usuario_raw)
    dni = str(dni_raw).strip()
    ttl = max(int(expires_in), 60)

    session.clear()
    if hasattr(session, "regenerate"):
        session.regenerate()  # type: ignore[attr-defined]

    session["id_usuario"] = id_usuario
    session["dni"] = dni
    session["access_token"] = access_token
    session["usuario"] = {
        "id": id_usuario,
        "id_usuario": id_usuario,
        "dni": dni,
        "nombre": usuario.get("nombre"),
        "apellido": usuario.get("apellido"),
        "email": usuario.get("email"),
        "rol": usuario.get("rol"),
    }
    session["_expires_at"] = time.time() + ttl


def cerrar_sesion_autenticada() -> None:
    """Limpia los datos de la sesión y elimina el archivo server-side y la cookie."""
    session.clear()


def sesion_paciente_activa() -> bool:
    """Indica si la sesión actual posee token vigente, `id_usuario` y `dni` válidos."""
    if not has_request_context():
        return False

    expires_at = session.get("_expires_at")
    if isinstance(expires_at, (int, float)) and expires_at <= time.time():
        cerrar_sesion_autenticada()
        return False

    token = session.get("access_token")
    id_usuario = session.get("id_usuario")
    dni = session.get("dni")

    if (
        not isinstance(token, str)
        or not token.strip()
        or isinstance(id_usuario, bool)
        or not isinstance(id_usuario, int)
        or id_usuario <= 0
        or not isinstance(dni, str)
        or not dni.strip()
    ):
        return False

    return True


def obtener_token_actual() -> str | None:
    """Devuelve el JWT vigente para la sesión actual o `None` si no hay sesión válida."""
    if not sesion_paciente_activa():
        return None
    token = session.get("access_token")
    return token if isinstance(token, str) and token else None


def obtener_usuario_actual() -> dict[str, Any] | None:
    """Devuelve los datos del usuario autenticado en la sesión actual o `None`."""
    if not sesion_paciente_activa():
        return None
    usuario = session.get("usuario")
    return dict(usuario) if isinstance(usuario, dict) else None


def construir_headers_autenticados() -> dict[str, str]:
    """Construye el encabezado `Authorization: Bearer <token>` para llamadas a la API."""
    token = obtener_token_actual()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def enviar(
    metodo: str,
    ruta: str,
    datos: dict[str, Any] | None = None,
    autenticado: bool = True,
) -> tuple[Any, int]:
    """Hace la llamada HTTP server-side a la API y devuelve `(contenido, status_code)`.

    Compatible con el contrato usado en `feature/administracion` y
    `feature/recepcion` (`get`, `post`, `patch`), adjuntando automáticamente el
    encabezado `Authorization: Bearer <token>` cuando existe sesión activa.
    """
    ruta_normalizada = ruta if ruta.startswith("/") else f"/{ruta}"
    url = f"{API_URL}{ruta_normalizada}"
    headers = construir_headers_autenticados() if autenticado else {}

    try:
        respuesta = requests.request(
            metodo,
            url,
            json=datos,
            headers=headers or None,
            timeout=TIMEOUT,
        )
    except requests.exceptions.RequestException:
        return {"error": "No se pudo conectar con el servidor"}, 503

    if respuesta.status_code == 401 and autenticado and has_request_context():
        cerrar_sesion_autenticada()

    try:
        contenido = respuesta.json()
    except ValueError:
        contenido = {"error": "La respuesta del servidor no es valida"}

    return contenido, respuesta.status_code


def get(ruta: str) -> tuple[Any, int]:
    """Hace un GET a la API."""
    return enviar("GET", ruta)


def post(ruta: str, datos: dict[str, Any] | None = None) -> tuple[Any, int]:
    """Hace un POST a la API."""
    return enviar("POST", ruta, datos)


def patch(ruta: str, datos: dict[str, Any] | None = None) -> tuple[Any, int]:
    """Hace un PATCH a la API."""
    return enviar("PATCH", ruta, datos)


def registrar_paciente_api(datos: dict[str, str]) -> tuple[dict[str, Any], int]:
    """Envía `POST /api/pacientes` al backend mediante `requests`."""
    payload = {
        "dni": datos.get("dni", ""),
        "nombre": datos.get("nombre", ""),
        "apellido": datos.get("apellido", ""),
        "email": datos.get("email", ""),
        "password": datos.get("password", ""),
    }
    try:
        response = requests.post(
            f"{BACKEND_API_URL}/pacientes",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        return response.json(), response.status_code
    except requests.RequestException:
        return {"error": "No se pudo conectar con el servidor de la clínica."}, 503
    except ValueError:
        return {"error": "Respuesta inválida del servidor."}, 502


def iniciar_sesion_api(email: str, password: str) -> tuple[dict[str, Any], int]:
    """Envía `POST /api/auth/login` al backend mediante `requests`."""
    try:
        response = requests.post(
            f"{BACKEND_API_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=REQUEST_TIMEOUT,
        )
        return response.json(), response.status_code
    except requests.RequestException:
        return {"error": "No se pudo conectar con el servidor de la clínica."}, 503
    except ValueError:
        return {"error": "Respuesta inválida del servidor."}, 502


def obtener_sesion_actual_api() -> tuple[dict[str, Any], int]:
    """Consulta `GET /api/auth/me` enviando el JWT en `Authorization: Bearer`."""
    headers = construir_headers_autenticados()
    if not headers:
        return {"error": "No autenticado."}, 401

    try:
        response = requests.get(
            f"{BACKEND_API_URL}/auth/me",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 401:
            cerrar_sesion_autenticada()
        return response.json(), response.status_code
    except requests.RequestException:
        return {"error": "No se pudo conectar con el servidor de la clínica."}, 503
    except ValueError:
        return {"error": "Respuesta inválida del servidor."}, 502
