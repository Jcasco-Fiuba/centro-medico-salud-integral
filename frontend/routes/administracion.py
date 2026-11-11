"""Rutas de administración del centro médico."""

from flask import Blueprint, redirect, render_template, url_for

from services.api_client import cerrar_sesion_autenticada, obtener_usuario_actual


administracion_bp = Blueprint("administracion", __name__, url_prefix="/administracion")


@administracion_bp.before_request
def exigir_sesion_admin_backoffice():
    """Exige sesión activa con rol `admin` para operar el módulo de administración."""
    usuario = obtener_usuario_actual()
    if usuario is None:
        cerrar_sesion_autenticada()
        return redirect(url_for("auth.iniciar_sesion"))
    if usuario.get("rol") != "admin":
        return ("No tiene permisos para acceder al módulo de administración.", 403)
    return None


@administracion_bp.get("/")
def inicio():
    """Muestra la vista mínima autenticada del módulo de administración."""
    return render_template("administracion/inicio.html", usuario=obtener_usuario_actual() or {})
