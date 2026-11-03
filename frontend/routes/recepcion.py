"""Rutas de recepción y sala de espera."""

from flask import Blueprint


recepcion_bp = Blueprint("recepcion", __name__, url_prefix="/recepcion")
