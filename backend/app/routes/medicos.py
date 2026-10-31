"""Rutas y endpoints para la entidad Médicos."""

from flask import Blueprint, jsonify

from app.constants import BASE_URL
from app.services import medicos as medicos_service
from app.validators.medicos import validar_id_medico

medicos_bp = Blueprint("medicos", __name__, url_prefix=BASE_URL)


@medicos_bp.route("/medicos", methods=["GET"])
def get_medicos():
    """Devuelve el listado de médicos."""
    try:
        medicos = medicos_service.listar_medicos()
    except NotImplementedError as error:
        return jsonify({"error": str(error)}), 501
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(medicos), 200


@medicos_bp.route("/medicos/<id>/baja", methods=["PATCH"])
def patch_medico_baja(id):
    """Solicita la baja de un médico por su ID."""
    try:
        id_medico = validar_id_medico(id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    try:
        resultado = medicos_service.dar_de_baja_medico(id_medico)
    except NotImplementedError as error:
        return jsonify({"error": str(error)}), 501
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(resultado), 200
