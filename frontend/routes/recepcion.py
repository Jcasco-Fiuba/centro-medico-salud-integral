"""Rutas de recepción y sala de espera."""

from flask import Blueprint, redirect, render_template, request, url_for

from services import api_client

recepcion_bp = Blueprint("recepcion", __name__, url_prefix="/recepcion")


@recepcion_bp.before_request
def exigir_sesion_admin_recepcion():
    """Exige sesión activa con rol `admin` para operar el módulo de recepción."""
    usuario = api_client.obtener_usuario_actual()
    if usuario is None:
        api_client.cerrar_sesion_autenticada()
        destino = api_client.construir_destino_actual(request, url_for("recepcion.checkin"))
        return redirect(url_for("auth.iniciar_sesion", next=destino))
    if usuario.get("rol") != "admin":
        return ("No tiene permisos para acceder al módulo de recepción.", 403)
    return None


def formatear_hora(valor):
    """Devuelve solo la hora (HH:MM) de una fecha que manda la API."""
    if not valor:
        return "-"

    if type(valor) != str:
        return str(valor)

    # La API manda las fechas asi: "Mon, 09 Nov 2026 10:00:00 GMT"
    partes = valor.split(" ")

    if len(partes) < 5:
        return valor

    return partes[4][:5]

def armar_turno(turno):
    """Arma los datos del turno que se muestran en pantalla."""
    paciente = ""
    if "paciente_nombre" in turno and "paciente_apellido" in turno:
        paciente = turno["paciente_nombre"] + " " + turno["paciente_apellido"]

    medico = ""
    if "medico_nombre" in turno and "medico_apellido" in turno:
        medico = turno["medico_nombre"] + " " + turno["medico_apellido"]

    dni = ""
    if "dni" in turno:
        dni = turno["dni"]

    estado = ""
    if "estado" in turno:
        estado = turno["estado"]

    return {
        "id": turno["id"],
        "paciente": paciente,
        "dni": dni,
        "medico": medico,
        "hora_turno": formatear_hora(turno["fecha_hora"]),
        "hora_checkin": formatear_hora(turno["hora_checkin"]),
        "estado": estado
    }

def obtener_error(respuesta, mensaje_por_defecto):
    """Devuelve el mensaje de error de la API o uno por defecto."""
    if type(respuesta) == dict and "error" in respuesta:
        return respuesta["error"]

    return mensaje_por_defecto

@recepcion_bp.get("/")
def inicio():
    """Entrada de recepción: lleva directo al check-in."""
    return redirect(url_for("recepcion.checkin"))

@recepcion_bp.get("/checkin")
def checkin():
    """Muestra el formulario para registrar la llegada con el código del QR."""
    return render_template("recepcion/checkin.html")

@recepcion_bp.post("/checkin")
def registrar_checkin():
    """Envía el código del QR a la API y muestra el resultado."""
    token = request.form.get("token", "").strip()

    if len(token) == 0:
        return render_template(
            "recepcion/checkin.html",
            tipo_mensaje="error",
            mensaje="Ingresá o escaneá el código del turno."
        ), 400

    respuesta, status = api_client.post("/api/turnos/checkin", {"string_token": token})

    if status != 200 or not isinstance(respuesta, dict):
        return render_template(
            "recepcion/checkin.html",
            tipo_mensaje="error",
            mensaje=obtener_error(respuesta, "No se pudo registrar la llegada."),
            token=token
        ), (status if status != 200 else 502)

    estado_turno = respuesta.get("estado")
    if estado_turno == "confirmado":
        tipo_mensaje = "success"
        mensaje = "Llegada registrada. El paciente pasó a la sala de espera."
    elif estado_turno == "ausente":
        tipo_mensaje = "warning"
        mensaje = "El paciente llegó fuera de horario. El turno quedó como ausente."
    else:
        tipo_mensaje = "success"
        mensaje = "Turno actualizado."

    return render_template(
        "recepcion/checkin.html",
        tipo_mensaje=tipo_mensaje,
        mensaje=mensaje,
        turno=armar_turno(respuesta)
    ), 200

@recepcion_bp.get("/sala-espera")
def sala_espera():
    """Muestra los pacientes confirmados del día, ordenados por llegada."""
    respuesta, status = api_client.get("/api/turnos/sala-espera")

    if status != 200 or not isinstance(respuesta, list):
        return render_template(
            "recepcion/sala_espera.html",
            turnos=[],
            tipo_mensaje="error",
            mensaje=obtener_error(respuesta, "No se pudo cargar la sala de espera.")
        ), (status if status != 200 else 502)

    turnos = []

    for turno in respuesta:
        turnos.append(armar_turno(turno))

    return render_template(
        "recepcion/sala_espera.html",
        turnos=turnos,
        tipo_mensaje=request.args.get("tipo_mensaje"),
        mensaje=request.args.get("mensaje")
    ), 200

@recepcion_bp.post("/turnos/<int:id>/atender")
def atender_turno(id):
    """Marca un turno como atendido y vuelve a la sala de espera."""
    respuesta, status = api_client.patch("/api/turnos/" + str(id) + "/atender")

    if status != 200:
        return redirect(url_for(
            "recepcion.sala_espera",
            tipo_mensaje="error",
            mensaje=obtener_error(respuesta, "No se pudo atender el turno.")
        ))

    return redirect(url_for(
        "recepcion.sala_espera",
        tipo_mensaje="success",
        mensaje="Turno marcado como atendido."
    ))
