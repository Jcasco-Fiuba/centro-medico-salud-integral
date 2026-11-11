"""Rutas de autenticación de pacientes."""

from flask import Blueprint, redirect, render_template, request, url_for

from services.api_client import (
    cerrar_sesion_autenticada,
    guardar_sesion_autenticada,
    iniciar_sesion_api,
    registrar_paciente_api,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _extraer_mensaje_error(respuesta: dict, fallback: str) -> str:
    """Extrae un mensaje de error legible desde `error` o `errores` del backend."""
    if not isinstance(respuesta, dict):
        return fallback
    error = respuesta.get("error")
    if isinstance(error, str) and error.strip():
        return error.strip()
    errores = respuesta.get("errores")
    if isinstance(errores, list) and errores:
        mensajes = [str(item).strip() for item in errores if str(item).strip()]
        if mensajes:
            return " · ".join(mensajes)
    return fallback


@auth_bp.get("/login")
def iniciar_sesion():
    """Muestra la pantalla de inicio de sesión."""
    return render_template("auth/login.html")


@auth_bp.post("/login")
def procesar_login():
    """Procesa las credenciales contra ``POST /api/auth/login`` y crea la sesión server-side."""
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    respuesta, status_code = iniciar_sesion_api(email=email, password=password)
    if status_code == 200 and "access_token" in respuesta:
        usuario = respuesta.get("usuario", {})
        guardar_sesion_autenticada(
            access_token=respuesta["access_token"],
            expires_in=int(respuesta.get("expires_in", 3600)),
            usuario=usuario,
        )
        if isinstance(usuario, dict) and usuario.get("rol") == "admin":
            return redirect(url_for("administracion.inicio"))
        return redirect(url_for("paciente.portal"))

    error = _extraer_mensaje_error(respuesta, "No se pudo iniciar sesión.")
    return render_template("auth/login.html", error=error), status_code


@auth_bp.get("/registro")
def registrarse():
    """Muestra el formulario de registro de pacientes."""
    return render_template("auth/registro.html")


@auth_bp.post("/registro")
def procesar_registro():
    """Envía los datos del formulario a ``POST /api/pacientes``."""
    password = request.form.get("password", "")
    repetir_password = request.form.get("repetir_password", "")
    if password != repetir_password:
        return (
            render_template(
                "auth/registro.html",
                error="Las contraseñas no coinciden.",
            ),
            400,
        )

    datos = {
        "nombre": request.form.get("nombre", "").strip(),
        "apellido": request.form.get("apellido", "").strip(),
        "dni": request.form.get("dni", "").strip(),
        "email": request.form.get("email", "").strip(),
        "password": password,
    }
    respuesta, status_code = registrar_paciente_api(datos)
    if status_code == 201:
        return redirect(url_for("auth.iniciar_sesion"))

    error = _extraer_mensaje_error(respuesta, "No se pudo completar el registro.")
    return render_template("auth/registro.html", error=error), status_code


@auth_bp.post("/logout")
def cerrar_sesion():
    """Cierra la sesión actual del usuario y elimina el token server-side."""
    cerrar_sesion_autenticada()
    return redirect(url_for("auth.iniciar_sesion"))
