from flask import Blueprint, jsonify, request

from app.services.turnos import (
    listar_turnos,
    obtener_turno,
    crear_turno
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