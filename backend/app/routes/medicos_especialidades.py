"""Rutas y endpoints para Especialidades."""

from flask import Blueprint, jsonify, request

from app.constants import BASE_URL
from app.services import medicos_especialidades as especialidades_service

especialidades_bp = Blueprint("especialidades", __name__, url_prefix=BASE_URL)


@especialidades_bp.route("/especialidades", methods=["GET"])
def get_especialidades():

    try:
        respuesta, status = especialidades_service.listar_especialidades()
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@especialidades_bp.route("/especialidades", methods=["POST"])
def post_especialidad():

    try:
        datos = request.get_json(silent=True)
        respuesta, status = especialidades_service.registrar_especialidad(datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status