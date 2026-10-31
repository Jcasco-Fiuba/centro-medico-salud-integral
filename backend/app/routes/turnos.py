from flask import Blueprint, jsonify, request, g

from app.services.turnos import (
    listar_turnos,
    obtener_turno,
    crear_turno,
    listar_turnos_disponibles,
    listar_sala_espera,
    atender_turno,
    cancelar_turno,
    reservar_turno
   
)

turnos_bp = Blueprint("turnos", __name__)


@turnos_bp.route("/api/turnos", methods=["GET"])
def get_turnos():

    medico = request.args.get("medico")
    estado = request.args.get("estado")

    try:
        turnos = listar_turnos(medico, estado)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(turnos), 200




@turnos_bp.route("/api/turnos/<int:id>", methods=["GET"])
def get_turno(id):

    turno = obtener_turno(id)

    if turno is None:
        return jsonify({"error": "Turno no encontrado"}), 404

    return jsonify(turno), 200



@turnos_bp.route("/api/turnos", methods=["POST"])
def post_turno():

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({"error": "JSON invalido"}), 400

    try:
        turno = crear_turno(datos)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(turno), 201

@turnos_bp.route("/api/turnos/disponibles", methods = ["GET"])
def get_turnos_disponibles():

    medico = request.args.get("medico")
    fecha = request.args.get("fecha")

    try:
        turnos = listar_turnos_disponibles(medico,fecha)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(turnos), 200    

@turnos_bp.route("/api/turnos/sala-espera", methods=["GET"])
def get_sala_espera():

    turnos = listar_sala_espera()

    return jsonify(turnos), 200

@turnos_bp.route("/api/turnos/<int:id>/atender", methods=["PATCH"])
def patch_atender_turno(id):

    try:
        turno = atender_turno(id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if turno is None:
        return jsonify({"error": "Turno no encontrado"}), 404

    return jsonify(turno), 200

@turnos_bp.route("/api/turnos/<int:id>/cancelar", methods=["PATCH"])
def patch_cancelar_turno(id):

    try:
        turno = cancelar_turno(id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if turno is None:
        return jsonify({"error": "Turno no encontrado"}), 404

    return jsonify(turno), 200



@turnos_bp.route("/api/turnos/reservar", methods=["POST"])
def post_reservar_turno():

    usuario = getattr(g, "usuario", None)

    if usuario is None:
        return jsonify({"error": "Debes iniciar sesion"}), 401

    if usuario.get("rol") != "paciente":
        return jsonify({"error": "No tienes permiso para reservar"}), 403

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({"error": "JSON invalido"}), 400

    turno_id = datos.get("turno_id")

    if not isinstance(turno_id, int) or turno_id <= 0:
        return jsonify({"error": "ID de turno invalido"}), 400

    try:
        turno = reservar_turno(turno_id, usuario["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if turno is None:
        return jsonify({"error": "Turno no encontrado"}), 404

    return jsonify(turno), 200