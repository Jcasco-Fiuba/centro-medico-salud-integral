from flask import Blueprint, request, jsonify

from app.constants import BASE_URL
from app.services.pacientes import (
    obtener_paciente,
    listar_pacientes,
    registrar_paciente,
    actualizar_paciente,
    dar_baja_paciente
)


pacientes_bp = Blueprint("pacientes", __name__, url_prefix=BASE_URL)


@pacientes_bp.route("/pacientes/<dni>", methods=["GET"])
def consultar_paciente(dni):
    """Consulta los datos de un paciente por su DNI."""

    try:
        respuesta, codigo = obtener_paciente(dni)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), codigo


@pacientes_bp.route("/pacientes", methods=["POST"])
def crear_paciente():
    """Registra un nuevo paciente."""

    datos = request.get_json(silent=True)

    if type(datos) != dict:
        return jsonify({"error": "El cuerpo debe ser un objeto JSON"}), 400

    try:
        respuesta, codigo = registrar_paciente(datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), codigo


@pacientes_bp.route("/pacientes/<dni>", methods=["PATCH"])
def modificar_paciente(dni):
    """Actualiza los datos de un paciente por su DNI."""

    datos = request.get_json(silent=True)

    if type(datos) != dict:
        return jsonify({"error": "El cuerpo debe ser un objeto JSON"}), 400

    try:
        respuesta, codigo = actualizar_paciente(dni, datos)
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify(respuesta), codigo


@pacientes_bp.route("/pacientes", methods=["GET"])
def listar():
    return listar_pacientes()


@pacientes_bp.route("/pacientes/<dni>/baja", methods=["PATCH"])
def baja(dni):
    return dar_baja_paciente(dni)
