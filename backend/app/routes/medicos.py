"""Rutas y endpoints para la entidad Médicos."""

from flask import Blueprint, jsonify, request

from app.constants import BASE_URL, ROL_ADMIN
from app.services import medicos as medicos_service
from app.services.auth_service import requiere_autenticacion
from app.validators.medicos import (
    validar_alta_medico,
    validar_id_medico,
    validar_modificacion_medico,
)

medicos_bp = Blueprint("medicos", __name__, url_prefix=BASE_URL)


@medicos_bp.route("/medicos", methods=["GET"])
def get_medicos():
    """Devuelve todos los médicos o los activos de una especialidad."""
    especialidad = request.args.get("especialidad")
    try:
        if especialidad is not None:
            if not (especialidad.isascii() and especialidad.isdigit()) or int(especialidad) <= 0:
                return (
                    jsonify({"error": "El ID de especialidad debe ser un entero positivo."}),
                    400,
                )
            medicos = medicos_service.listar_medicos_por_especialidad(int(especialidad))
        else:
            medicos = medicos_service.listar_medicos()
    except NotImplementedError as error:
        return jsonify({"error": str(error)}), 501
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(medicos), 200


@medicos_bp.route("/medicos/<id>", methods=["GET"])
def get_medico(id):
    """Devuelve información de un médico por su ID."""
    try:
        id_medico = validar_id_medico(id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    try:
        medico = medicos_service.obtener_medico(id_medico)
    except NotImplementedError as error:
        return jsonify({"error": str(error)}), 501
    except Exception:
        return jsonify({"error": "Error del servidor"}), 500

    if medico is None:
        return jsonify({"error": "Médico no encontrado"}), 404
    return jsonify(medico), 200


@medicos_bp.route("/medicos", methods=["POST"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def post_medico():
    """Da de alta un médico con sus especialidades (exclusivo `admin`)."""
    try:
        datos = validar_alta_medico(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    try:
        medico = medicos_service.crear_medico(datos)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except NotImplementedError as error:
        return jsonify({"error": str(error)}), 501
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(medico), 201


@medicos_bp.route("/medicos/<id>", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def patch_medico(id):
    """Modifica la información de un médico (exclusivo `admin`)."""
    try:
        id_medico = validar_id_medico(id)
        cambios = validar_modificacion_medico(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    try:
        medico = medicos_service.modificar_medico(id_medico, cambios)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except NotImplementedError as error:
        return jsonify({"error": str(error)}), 501
    except Exception:
        return jsonify({"error": "Error del servidor"}), 500

    if not medico:
        return jsonify({"error": "Médico no encontrado"}), 404
    return jsonify(medico), 200


@medicos_bp.route("/medicos/<id>/baja", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def patch_medico_baja(id):
    """Solicita la baja lógica de un médico por su ID (exclusivo `admin`)."""
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

    if resultado is None:
        return jsonify({"error": "Médico no encontrado"}), 404
    return jsonify(resultado), 200
