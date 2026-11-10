"""Rutas y endpoints para la entidad Consultorios."""

from flask import Blueprint, jsonify, request

from app.constants import BASE_URL
from app.services import consultorios as consultorios_service

consultorios_bp = Blueprint("consultorios", __name__, url_prefix=BASE_URL)


@consultorios_bp.route("/consultorios", methods=["GET"])
def get_consultorios():

    try:
        respuesta, status = consultorios_service.listar_consultorios()
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@consultorios_bp.route("/consultorios/<id>", methods=["GET"])
def get_consultorio(id):

    try:
        respuesta, status = consultorios_service.obtener_consultorio(id)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@consultorios_bp.route("/consultorios", methods=["POST"])
def post_consultorio():
    
    try:
        datos = request.get_json(silent=True)
        respuesta, status = consultorios_service.registrar_consultorio(datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@consultorios_bp.route("/consultorios/<id>", methods=["PATCH"])

def patch_consultorio(id):
    
    try:
        datos = request.get_json(silent=True)
        respuesta, status = consultorios_service.actualizar_consultorio(id, datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status


@consultorios_bp.route("/consultorios/<id>/baja", methods=["PATCH"])
def patch_baja_consultorio(id):
    try:
        respuesta, status = consultorios_service.dar_de_baja_consultorio(id)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), status