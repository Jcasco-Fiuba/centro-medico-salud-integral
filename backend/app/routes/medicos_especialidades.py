"""Rutas y endpoints para la entidad Medicos-Especialidades."""

from flask import Blueprint, jsonify, request

from app.constants import BASE_URL
from app.services import medicos_especialidades as medicos_service
from app.validators.medicos_especialidades import ( 
    validar_id_medico, 
    validar_alta_medico, 
    validar_modificacion_medico, 
    )

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

@medicos_bp.route("/medicos/<id>", methods=["GET"])
def get_medico(id):
   """devuelve informacion de un medico por su id"""
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
def post_medico():
    """da el alta de un médico con sus especialidades"""
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
def patch_medico(id):
    """modifica la informcion enviada de un medico"""
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

    if medico is None:
        return jsonify({"error": "Médico no encontrado"}), 404
    return jsonify(medico), 200