"""Rutas de autenticación de pacientes."""

from flask import Blueprint, render_template


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def iniciar_sesion():
    """Muestra la pantalla de inicio de sesión."""
    return render_template("auth/login.html")


@auth_bp.get("/registro")
def registrarse():
    """Muestra el formulario de registro de pacientes."""
    return render_template("auth/registro.html")
