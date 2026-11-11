"""Rutas y endpoints para la entidad Turnos."""

from flask import Blueprint, g, jsonify, request

from app.constants import BASE_URL, ROL_ADMIN, ROL_PACIENTE
from app.services.auth_service import requiere_autenticacion
from app.services.turnos import (
    atender_turno,
    cancelar_turno,
    crear_turno,
    listar_sala_espera,
    listar_turnos,
    listar_turnos_disponibles,
    obtener_turno,
    realizar_checkin,
    reservar_turno,
)

turnos_bp = Blueprint("turnos", __name__, url_prefix=BASE_URL)


@turnos_bp.route("/turnos", methods=["GET"])
@requiere_autenticacion(roles=(ROL_PACIENTE, ROL_ADMIN))
def get_turnos():
    """Lista turnos. Si el usuario es `paciente`, restringe la consulta a sus propios turnos."""
    medico = request.args.get("medico")
    estado = request.args.get("estado")
    dni = request.args.get("dni")

    usuario = g.usuario_actual
    if usuario["rol"] == ROL_PACIENTE:
        if dni is not None and str(dni).strip() != str(usuario["dni"]):
            return jsonify({"error": "No tiene permisos para consultar turnos de otro paciente."}), 403
        dni = str(usuario["dni"])

    try:
        turnos = listar_turnos(medico=medico, estado=estado, dni=dni)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500
    return jsonify(turnos), 200


@turnos_bp.route("/turnos/<int:id>", methods=["GET"])
@requiere_autenticacion(roles=(ROL_PACIENTE, ROL_ADMIN))
def get_turno(id: int):
    """Obtiene el detalle de un turno (el propio paciente o `admin`)."""
    try:
        turno = obtener_turno(id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    if turno is None:
        return jsonify({"error": "Turno no encontrado"}), 404

    usuario = g.usuario_actual
    if usuario["rol"] == ROL_PACIENTE and turno.get("id_usuario") != usuario["id"]:
        return jsonify({"error": "No tiene permisos para consultar este turno."}), 403

    return jsonify(turno), 200


@turnos_bp.route("/turnos", methods=["POST"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def post_turno():
    """Crea un turno disponible en la agenda (exclusivo `admin`)."""
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "El cuerpo debe ser un objeto JSON"}), 400
    try:
        turno, mensaje = crear_turno(datos)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500
    if mensaje is not None:
        return jsonify({"error": mensaje}), 400
    return jsonify(turno), 201


@turnos_bp.route("/turnos/disponibles", methods=["GET"])
def get_turnos_disponibles():
    """Consulta pública de turnos disponibles por médico y fecha (no requiere login)."""
    try:
        turnos = listar_turnos_disponibles(
            request.args.get("medico"),
            request.args.get("fecha"),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500
    return jsonify(turnos), 200


@turnos_bp.route("/turnos/reservar", methods=["POST"])
@requiere_autenticacion(roles=(ROL_PACIENTE,))
def post_reservar_turno():
    """Reserva un turno disponible asignándolo al paciente autenticado en el JWT."""
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "El cuerpo debe ser un objeto JSON"}), 400

    usuario_id = int(g.usuario_actual["id"])
    try:
        turno, error = reservar_turno(datos, usuario_id=usuario_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    if error is not None:
        return jsonify({"error": error}), 400
    return jsonify(turno), 200


@turnos_bp.route("/turnos/<int:id>/cancelar", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_PACIENTE, ROL_ADMIN))
def patch_cancelar_turno(id: int):
    """Cancela un turno reservado (el propio paciente titular o `admin`)."""
    usuario = g.usuario_actual
    usuario_id = int(usuario["id"]) if usuario["rol"] == ROL_PACIENTE else None

    try:
        turno = cancelar_turno(id, usuario_id=usuario_id)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    if turno is None:
        return jsonify({"error": "Turno no encontrado"}), 404
    return jsonify(turno), 200


@turnos_bp.route("/turnos/checkin", methods=["POST"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def post_checkin():
    """Valida el token QR en recepción dentro de la ventana de 15 minutos (exclusivo `admin`)."""
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "El cuerpo debe ser un objeto JSON"}), 400

    try:
        turno = realizar_checkin(datos)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    if turno is None:
        return jsonify({"error": "Turno no encontrado"}), 404
    return jsonify(turno), 200


@turnos_bp.route("/turnos/sala-espera", methods=["GET"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def get_sala_espera():
    """Lista los turnos confirmados del día en sala de espera (exclusivo `admin`)."""
    try:
        return jsonify(listar_sala_espera()), 200
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500


@turnos_bp.route("/turnos/<int:id>/atender", methods=["PATCH"])
@requiere_autenticacion(roles=(ROL_ADMIN,))
def patch_atender_turno(id: int):
    """Marca un turno confirmado como atendido (exclusivo `admin`)."""
    try:
        turno = atender_turno(id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500

    if turno is None:
        return jsonify({"error": "Turno no encontrado"}), 404
    return jsonify(turno), 200
