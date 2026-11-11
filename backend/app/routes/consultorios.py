"""Rutas y endpoints para la entidad Consultorios."""

from flask import Blueprint, jsonify, request

from app.constants import BASE_URL, ROL_ADMIN
from app.services import consultorios as consultorios_service
from app.services.auth_service import requiere_autenticacion

consultorios_bp = Blueprint("consultorios", __name__, url_prefix=BASE_URL)


@consultorios_bp.route("/consultorios", methods=["GET"])
def get_consultorios():
    """Devuelve el listado de consultorios."""
    try:
        respuesta, status = consultorios_service.listar_consultorios()
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@consultorios_bp.route("/consultorios/<id>", methods=["GET"])
def get_consultorio(id):
    """Devuelve el detalle de un consultorio por su ID."""
    try:
        respuesta, status = consultorios_service.obtener_consultorio(id)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@consultorios_bp.route("/consultorios", methods=["POST"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def post_consultorio():
    """Da de alta un nuevo consultorio (exclusivo `admin`)."""
    try:
        datos = request.get_json(silent=True)
        respuesta, status = consultorios_service.registrar_consultorio(datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@consultorios_bp.route("/consultorios/<id>", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def patch_consultorio(id):
    """Modifica los datos de un consultorio (exclusivo `admin`)."""
    try:
        datos = request.get_json(silent=True)
        respuesta, status = consultorios_service.actualizar_consultorio(id, datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@consultorios_bp.route("/consultorios/<id>/baja", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def patch_baja_consultorio(id):
    """Solicita la baja de un consultorio por su ID (exclusivo `admin`)."""
    try:
        respuesta, status = consultorios_service.dar_de_baja_consultorio(id)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status
