"""Rutas del portal autenticado de pacientes."""

from flask import Blueprint, redirect, url_for

from services.api_client import cerrar_sesion_autenticada, sesion_paciente_activa


paciente_bp = Blueprint("paciente", __name__, url_prefix="/paciente")


@paciente_bp.before_request
def exigir_sesion_paciente():
    """Exige una sesión autenticada válida antes de entrar a cualquier ruta de `/paciente`.

    Conserva `session["id_usuario"]` y `session["dni"]` establecidos por el login
    para que las vistas del portal de paciente los consuman, y solo limpia la
    sesión cuando es inválida, está vencida o no posee JWT.
    """
    if not sesion_paciente_activa():
        cerrar_sesion_autenticada()
        return redirect(url_for("auth.iniciar_sesion"))
    return None
