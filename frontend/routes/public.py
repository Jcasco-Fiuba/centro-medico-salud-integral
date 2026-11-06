"""Rutas públicas: información del centro y consulta de disponibilidad."""

from flask import Blueprint, render_template


public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def inicio():
    """Muestra el menú público principal del centro médico."""
    return render_template("public/inicio.html")
