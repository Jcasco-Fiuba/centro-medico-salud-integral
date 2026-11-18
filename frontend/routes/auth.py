"""Rutas de autenticación de pacientes."""

import re

from flask import Blueprint, redirect, render_template, request, url_for

from services.api_client import (
    cerrar_sesion_autenticada,
    guardar_sesion_autenticada,
    iniciar_sesion_api,
    limpiar_destino_next,
    registrar_paciente_api,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_DNI_REGEX = re.compile(r"^\d{7,8}$")


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


def _aviso_contexto_login(next_url: str) -> str:
    """Devuelve un mensaje contextual cuando el usuario llega redirigido desde una gestión."""
    if not next_url:
        return ""
    if next_url.startswith("/paciente/reservar"):
        return "Iniciá sesión o creá tu cuenta para continuar con tu reserva."
    if next_url.startswith(("/paciente/mis-turnos", "/paciente/turnos")):
        return "Iniciá sesión para consultar y gestionar tus turnos."
    return "Iniciá sesión para continuar con tu gestión."


def _validar_formulario_registro(valores: dict, password: str, repetir_password: str) -> dict[str, str]:
    """Valida campos obligatorios y formato del registro antes de invocar la API."""
    errores: dict[str, str] = {}
    if not valores["nombre"]:
        errores["nombre"] = "! Ingresá tu nombre."
    if not valores["apellido"]:
        errores["apellido"] = "! Ingresá tu apellido."

    dni = valores["dni"]
    if not dni:
        errores["dni"] = "! Ingresá tu DNI."
    elif not _DNI_REGEX.match(dni):
        errores["dni"] = "! Ingresá un DNI válido de 7 u 8 números."

    email = valores["email"]
    if not email:
        errores["email"] = "! Ingresá tu correo electrónico."
    elif not _EMAIL_REGEX.match(email):
        errores["email"] = "! Ingresá un correo electrónico válido."

    if not password:
        errores["password"] = "! Ingresá tu contraseña."
    elif len(password) < 8:
        errores["password"] = "! La contraseña debe tener al menos 8 caracteres."

    if not repetir_password:
        errores["repetir_password"] = "! Repetí tu contraseña."
    elif password and password != repetir_password:
        errores["repetir_password"] = "! Las contraseñas no coinciden. Volvé a escribirlas."

    if not valores["terminos"]:
        errores["terminos"] = "! Para crear tu cuenta, aceptá los términos y la política de privacidad."

    return errores


@auth_bp.get("/login")
def iniciar_sesion():
    """Muestra la pantalla de inicio de sesión."""
    next_url = limpiar_destino_next(request.args.get("next"))
    aviso_registro = request.args.get("registrado") == "1"
    return render_template(
        "auth/login.html",
        next_url=next_url,
        aviso_registro=aviso_registro,
        aviso_contexto=_aviso_contexto_login(next_url),
        email="",
        remember=False,
        field_errors={},
    )


@auth_bp.post("/login")
def procesar_login():
    """Procesa las credenciales contra ``POST /api/auth/login`` y crea la sesión server-side."""
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    recordarme = request.form.get("remember") in ("on", "1", "true", "True")
    next_url = limpiar_destino_next(request.form.get("next") or request.args.get("next"))
    aviso_contexto = _aviso_contexto_login(next_url)

    field_errors: dict[str, str] = {}
    if not email:
        field_errors["email"] = "! Ingresá tu correo electrónico."
    elif not _EMAIL_REGEX.match(email):
        field_errors["email"] = "! Ingresá un correo electrónico válido."
    if not password:
        field_errors["password"] = "! Ingresá tu contraseña."

    if field_errors:
        return (
            render_template(
                "auth/login.html",
                error="Revisá los datos ingresados e intentá nuevamente.",
                field_errors=field_errors,
                email=email,
                remember=recordarme,
                next_url=next_url,
                aviso_contexto=aviso_contexto,
            ),
            400,
        )

    respuesta, status_code = iniciar_sesion_api(
        email=email,
        password=password,
        recordarme=recordarme,
    )
    if status_code == 200 and "access_token" in respuesta:
        usuario = respuesta.get("usuario", {})
        guardar_sesion_autenticada(
            access_token=respuesta["access_token"],
            expires_in=int(respuesta.get("expires_in", 3600)),
            usuario=usuario,
            recordarme=recordarme,
        )
        es_admin = isinstance(usuario, dict) and usuario.get("rol") == "admin"
        destino_seguro = next_url
        if destino_seguro.startswith(("/administracion", "/recepcion")) and not es_admin:
            destino_seguro = ""
        if destino_seguro:
            return redirect(destino_seguro)
        if es_admin:
            return redirect(url_for("administracion.inicio"))
        return redirect(url_for("paciente.portal"))

    error = _extraer_mensaje_error(respuesta, "No se pudo iniciar sesión.")
    return (
        render_template(
            "auth/login.html",
            error=error,
            field_errors={},
            email=email,
            remember=recordarme,
            next_url=next_url,
            aviso_contexto=aviso_contexto,
        ),
        status_code,
    )


@auth_bp.get("/registro")
def registrarse():
    """Muestra el formulario de registro de pacientes."""
    next_url = limpiar_destino_next(request.args.get("next"))
    return render_template(
        "auth/registro.html",
        next_url=next_url,
        valores={},
        field_errors={},
    )


@auth_bp.post("/registro")
def procesar_registro():
    """Envía los datos del formulario a ``POST /api/pacientes``."""
    next_url = limpiar_destino_next(request.form.get("next") or request.args.get("next"))
    password = request.form.get("password", "")
    repetir_password = request.form.get("repetir_password", "")
    acepta_terminos = request.form.get("terminos") in ("on", "1", "true", "True")

    valores = {
        "nombre": request.form.get("nombre", "").strip(),
        "apellido": request.form.get("apellido", "").strip(),
        "dni": request.form.get("dni", "").strip(),
        "email": request.form.get("email", "").strip(),
        "terminos": acepta_terminos,
    }

    field_errors = _validar_formulario_registro(valores, password, repetir_password)
    if field_errors:
        mensaje = next(iter(field_errors.values())).lstrip("! ").strip()
        if "repetir_password" in field_errors and "coinciden" in field_errors["repetir_password"]:
            mensaje = "Las contraseñas no coinciden."
        elif "terminos" in field_errors and len(field_errors) == 1:
            mensaje = "Debés aceptar los términos y condiciones y la política de privacidad."
        return (
            render_template(
                "auth/registro.html",
                error=mensaje,
                field_errors=field_errors,
                valores=valores,
                next_url=next_url,
            ),
            400,
        )

    datos = {
        "nombre": valores["nombre"],
        "apellido": valores["apellido"],
        "dni": valores["dni"],
        "email": valores["email"],
        "password": password,
        "acepta_terminos": acepta_terminos,
    }
    respuesta, status_code = registrar_paciente_api(datos)
    if status_code == 201:
        destino = (
            url_for("auth.iniciar_sesion", next=next_url, registrado="1")
            if next_url
            else url_for("auth.iniciar_sesion", registrado="1")
        )
        return redirect(destino)

    error = _extraer_mensaje_error(respuesta, "No se pudo completar el registro.")
    return (
        render_template(
            "auth/registro.html",
            error=error,
            field_errors={},
            valores=valores,
            next_url=next_url,
        ),
        status_code,
    )


@auth_bp.post("/logout")
def cerrar_sesion():
    """Cierra la sesión actual del usuario y elimina el token server-side."""
    cerrar_sesion_autenticada()
    return redirect(url_for("auth.iniciar_sesion"))
