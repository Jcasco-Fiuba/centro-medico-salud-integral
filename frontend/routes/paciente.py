"""Rutas del portal autenticado de pacientes."""
from datetime import datetime, timedelta
import requests

from flask import Blueprint, render_template, session


paciente_bp = Blueprint("paciente", __name__, url_prefix="/paciente")
