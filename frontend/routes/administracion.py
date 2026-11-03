"""Rutas de administración del centro médico."""

from flask import Blueprint


administracion_bp = Blueprint("administracion", __name__, url_prefix="/administracion")
