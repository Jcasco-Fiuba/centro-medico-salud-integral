"""Rutas de autenticación de la API (login y verificación de sesión)."""

import logging

from flask import Blueprint, g, jsonify, request
import mysql.connector

from app.constants import BASE_URL
from app.services.auth_service import (
    CredencialesInvalidasError,
    autenticar_usuario,
    requiere_autenticacion,
)
from app.services.jwt_service import JWTConfigError
from app.validators.auth_validators import validar_payload_login

logger = logging.getLogger(__name__)

auth_api_bp = Blueprint("auth_api", __name__, url_prefix=f"{BASE_URL}/auth")


@auth_api_bp.post("/login")
def login():
    """Autentica un usuario activo y devuelve un JWT (``POST /api/auth/login``)."""
    if not request.is_json:
        return jsonify({"error": "El cuerpo de la solicitud debe enviarse en formato JSON."}), 400

    payload = request.get_json(silent=True)
    datos, error_validacion = validar_payload_login(payload)
    if error_validacion is not None or datos is None:
        return jsonify({"error": error_validacion}), 400

    try:
        resultado = autenticar_usuario(datos["email"], datos["password"])
    except CredencialesInvalidasError as exc:
        return jsonify({"error": str(exc)}), 401
    except JWTConfigError:
        logger.error("Error de configuración JWT al emitir token en login.")
        return jsonify({"error": "Error de configuración del servidor."}), 500
    except mysql.connector.Error:
        logger.error("Error de base de datos durante el inicio de sesión.")
        return jsonify({"error": "Error interno al procesar el inicio de sesión."}), 500

    return jsonify(resultado), 200


@auth_api_bp.get("/me")
@requiere_autenticacion()
def obtener_sesion_actual():
    """Devuelve los datos del usuario autenticado derivados del JWT y verificados en MySQL."""
    return jsonify({"usuario": g.usuario_actual}), 200
