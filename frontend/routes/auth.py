"""Rutas de autenticación de pacientes."""

from flask import Blueprint


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
