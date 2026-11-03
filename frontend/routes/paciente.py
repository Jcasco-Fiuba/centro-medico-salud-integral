"""Rutas del portal autenticado de pacientes."""

from flask import Blueprint


paciente_bp = Blueprint("paciente", __name__, url_prefix="/paciente")
