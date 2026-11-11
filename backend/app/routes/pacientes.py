"""Rutas unificadas de la API para registro, perfil y ABM de pacientes."""

import logging

from flask import Blueprint, g, jsonify, request
import mysql.connector

from app.constants import BASE_URL, ROL_ADMIN, ROL_PACIENTE
from app.services.auth_service import (
    EstadoPacienteConflictoError,
    PacienteNoEncontradoError,
    UsuarioDuplicadoError,
    actualizar_perfil_paciente,
    dar_baja_logica_paciente,
    listar_pacientes_registrados,
    obtener_perfil_paciente,
    registrar_paciente,
    requiere_autenticacion,
)
from app.validators.auth_validators import (
    validar_dni,
    validar_payload_actualizacion_paciente,
    validar_payload_registro_paciente,
)

logger = logging.getLogger(__name__)

pacientes_bp = Blueprint("pacientes", __name__, url_prefix=BASE_URL)


def _es_propietario_o_admin(dni_objetivo: str) -> bool:
    """Verifica que el usuario autenticado sea `admin` o titular del DNI consultado."""
    usuario = getattr(g, "usuario_actual", None)
    if not isinstance(usuario, dict):
        return False
    if usuario.get("rol") == ROL_ADMIN:
        return True
    return str(usuario.get("dni")) == str(dni_objetivo)


@pacientes_bp.route("/pacientes", methods=["POST"])
def crear_paciente():
    """Registra un nuevo paciente (``POST /api/pacientes``)."""
    if not request.is_json:
        return jsonify({"error": "El cuerpo de la solicitud debe enviarse en formato JSON."}), 400

    payload = request.get_json(silent=True)
    datos, error_validacion = validar_payload_registro_paciente(payload)
    if error_validacion is not None or datos is None:
        return jsonify({"error": error_validacion}), 400

    try:
        paciente = registrar_paciente(datos)
    except UsuarioDuplicadoError as exc:
        return jsonify({"error": str(exc)}), 409
    except mysql.connector.Error:
        logger.error("Error de base de datos durante el registro de paciente.")
        return jsonify({"error": "Error interno al registrar el paciente."}), 500

    return (
        jsonify(
            {
                "mensaje": "Paciente registrado correctamente.",
                "paciente": paciente,
            }
        ),
        201,
    )


@pacientes_bp.route("/pacientes/<dni>", methods=["GET"])
@requiere_autenticacion(roles=(ROL_PACIENTE, ROL_ADMIN))
def consultar_paciente(dni: str):
    """Consulta el perfil de un paciente por su DNI (solo el propio paciente o `admin`)."""
    try:
        dni_limpio = validar_dni(dni)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not _es_propietario_o_admin(dni_limpio):
        return jsonify({"error": "No tiene permisos para consultar los datos de otro paciente."}), 403

    try:
        paciente = obtener_perfil_paciente(dni_limpio)
    except PacienteNoEncontradoError as exc:
        return jsonify({"error": str(exc)}), 404
    except mysql.connector.Error:
        logger.error("Error de base de datos al consultar paciente.")
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify({"paciente": paciente}), 200


@pacientes_bp.route("/pacientes/<dni>", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_PACIENTE, ROL_ADMIN))
def modificar_paciente(dni: str):
    """Actualiza nombre, apellido o email de un paciente (solo el propio paciente o `admin`)."""
    try:
        dni_limpio = validar_dni(dni)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not _es_propietario_o_admin(dni_limpio):
        return jsonify({"error": "No tiene permisos para modificar los datos de otro paciente."}), 403

    if not request.is_json:
        return jsonify({"error": "El cuerpo de la solicitud debe enviarse en formato JSON."}), 400

    payload = request.get_json(silent=True)
    datos, error_validacion = validar_payload_actualizacion_paciente(payload)
    if error_validacion is not None or datos is None:
        return jsonify({"error": error_validacion}), 400

    try:
        actualizar_perfil_paciente(dni_limpio, datos)
    except PacienteNoEncontradoError as exc:
        return jsonify({"error": str(exc)}), 404
    except UsuarioDuplicadoError as exc:
        return jsonify({"error": str(exc)}), 409
    except mysql.connector.Error:
        logger.error("Error de base de datos al actualizar paciente.")
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify({"mensaje": "Paciente actualizado correctamente."}), 200


@pacientes_bp.route("/pacientes", methods=["GET"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def listar():
    """Devuelve el listado de pacientes (exclusivo `admin`)."""
    try:
        pacientes = listar_pacientes_registrados()
    except mysql.connector.Error:
        logger.error("Error de base de datos al listar pacientes.")
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify({"pacientes": pacientes}), 200


@pacientes_bp.route("/pacientes/<dni>/baja", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def baja(dni: str):
    """Da de baja lógica a un paciente por su DNI (exclusivo `admin`)."""
    try:
        dni_limpio = validar_dni(dni)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        dar_baja_logica_paciente(dni_limpio)
    except PacienteNoEncontradoError as exc:
        return jsonify({"error": str(exc)}), 404
    except EstadoPacienteConflictoError as exc:
        return jsonify({"error": str(exc)}), 409
    except mysql.connector.Error:
        logger.error("Error de base de datos al dar de baja paciente.")
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify({"mensaje": "Paciente dado de baja correctamente."}), 200
