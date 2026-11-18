"""Rutas y endpoints para Especialidades."""

from flask import Blueprint, jsonify, request

from app.constants import BASE_URL, ROL_ADMIN
from app.services import medicos_especialidades as especialidades_service
from app.services.auth_service import requiere_autenticacion

especialidades_bp = Blueprint("especialidades", __name__, url_prefix=BASE_URL)


@especialidades_bp.route("/especialidades", methods=["GET"])
def get_especialidades():
    """Devuelve el listado de especialidades médicas."""
    try:
        respuesta, status = especialidades_service.listar_especialidades()
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@especialidades_bp.route("/especialidades/<id>", methods=["GET"])
def get_especialidad(id):
    """Devuelve una especialidad por su ID."""
    try:
        respuesta, status = especialidades_service.obtener_especialidad(id)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@especialidades_bp.route("/especialidades", methods=["POST"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def post_especialidad():
    """Da de alta una nueva especialidad médica (exclusivo `admin`)."""
    try:
        datos = request.get_json(silent=True)
        respuesta, status = especialidades_service.registrar_especialidad(datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@especialidades_bp.route("/especialidades/<id>", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def patch_especialidad(id):
    """Modifica una especialidad; con `activo` en `false` se da de baja (exclusivo `admin`)."""
    try:
        datos = request.get_json(silent=True)
        respuesta, status = especialidades_service.actualizar_especialidad(id, datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status
