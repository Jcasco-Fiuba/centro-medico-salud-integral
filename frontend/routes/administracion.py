"""Rutas de administración del centro médico."""

from flask import Blueprint,render_template,request


administracion_bp = Blueprint("administracion", __name__, url_prefix="/administracion")


@administracion_bp.route("/agendas")
def agendas():
    medico = request.args.get("medico")
    estado = request.args.get("estado")

    return render_template(
        "administracion/agendas.html",
        medico=medico,
        estado=estado
    )

@administracion_bp.route("/agendas/nueva")
def nueva_agenda():
    return render_template(
        "administracion/formulario_agenda.html",
        editando=False
    )

@administracion_bp.route("/permisos")
def permisos():
    return render_template("administracion/permisos.html")

@administracion_bp.route("/acceso-denegado")
def acceso_denegado():
    return render_template("administracion/acceso_denegado.html"), 403

@administracion_bp.route("/agendas/<int:id>/editar")
def editar_agenda(id):
    return render_template(
        "administracion/formulario_agenda.html",
        editando=True
    )