"""Rutas de administración del centro médico."""

from flask import Blueprint,render_template,request,redirect,url_for
from services import api_client
from urllib.parse import urlencode
from datetime import datetime


administracion_bp = Blueprint("administracion", __name__, url_prefix="/administracion")


def cargar_opciones_agenda():

    respuesta_medicos, status_medicos = api_client.get("/api/medicos")
    respuesta_consultorios, status_consultorios = api_client.get("/api/consultorios")

    medicos = []
    consultorios = []

    if status_medicos == 200 and isinstance(respuesta_medicos, list):
        medicos = respuesta_medicos

    if status_consultorios == 200 and isinstance(respuesta_consultorios, dict):
        consultorios = respuesta_consultorios.get("consultorios", [])

    return medicos, consultorios

@administracion_bp.route("/agendas")
def agendas():

    medico = request.args.get("medico", "")
    estado = request.args.get("estado", "")

    filtros = {}

    if medico:
        filtros["medico"] = medico

    if estado:
        filtros["estado"] = estado

    ruta = "/api/turnos"

    if filtros:
        ruta = ruta + "?" + urlencode(filtros)

    respuesta, status = api_client.get(ruta)

    error = None
    turnos = []

    if status == 200 and isinstance(respuesta, list):
        turnos = respuesta
    else:
        error = "No se pudieron cargar los turnos."

    respuesta_medicos, status_medicos = api_client.get("/api/medicos")

    medicos = []
    error_medicos = None

    if status_medicos == 200 and isinstance(respuesta_medicos, list):
        medicos = respuesta_medicos
    else:
        error_medicos = "No se pudieron cargar los médicos."


    return render_template(
        "administracion/agendas.html",
        medico=medico,
        estado=estado,
        turnos=turnos,
        error=error,
        medicos=medicos,
        error_medicos=error_medicos
    )

@administracion_bp.route("/agendas/nueva")
def nueva_agenda():

    medicos, consultorios = cargar_opciones_agenda()

    return render_template(
        "administracion/formulario_agenda.html",
        editando=False,
        medicos=medicos,
        consultorios=consultorios
    )



@administracion_bp.route("/agendas/<int:id>/editar")
def editar_agenda(id):

    medicos, consultorios = cargar_opciones_agenda()

    return render_template(
        "administracion/formulario_agenda.html",
        editando=True,
        medicos=medicos,
        consultorios=consultorios
    )

@administracion_bp.route("/agendas/disponibilidad")
def disponibilidad():

    medico = request.args.get("medico", "")
    fecha = request.args.get("fecha", "")

    turnos = []
    error = None

    if medico and fecha:

        ruta = "/api/turnos/disponibles?" + urlencode({
            "medico": medico,
            "fecha": fecha
        })

        respuesta, status = api_client.get(ruta)

        if status == 200 and isinstance(respuesta, list):
            turnos = respuesta
        else:
            error = "No se pudo consultar la disponibilidad."

    medicos,_ = cargar_opciones_agenda()

    return render_template(
        "administracion/disponibilidad.html",
        medico=medico,
        fecha=fecha,
        turnos=turnos,
        medicos=medicos,
        error=error
    )

@administracion_bp.get("/turnos/nuevo")
def nuevo_turno():

    medicos, consultorios = cargar_opciones_agenda()

    return render_template(
        "administracion/crear_turno.html",
        medicos=medicos,
        consultorios=consultorios,
        error=None
    )

@administracion_bp.post("/turnos/nuevo")
def guardar_turno():

    medico = request.form.get("medico", "")
    consultorio = request.form.get("consultorio", "")
    fecha = request.form.get("fecha", "")
    hora = request.form.get("hora", "")

    error = None

    if not medico.isdigit() or not consultorio.isdigit() or not fecha or not hora:
        error = "Completá correctamente todos los campos."

    elif int(medico) <= 0 or int(consultorio) <= 0:
        error = "Seleccioná un médico y un consultorio válidos."

    else:

        try:
            fecha_hora = datetime.strptime(fecha + " " + hora, "%Y-%m-%d %H:%M")

            datos = {
                "id_medico": int(medico),
                "id_consultorio": int(consultorio),
                "fecha_hora": fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
            }

            respuesta, status = api_client.post("/api/turnos", datos)

            if status == 201:
                return redirect(url_for("administracion.agendas", creado="1"))

            if isinstance(respuesta, dict):
                error = respuesta.get("error", "No se pudo crear el turno.")
            else:
                error = "No se pudo crear el turno."

        except ValueError:
            error = "La fecha o la hora ingresadas no son válidas."

    medicos, consultorios = cargar_opciones_agenda()

    return render_template(
        "administracion/crear_turno.html",
        medicos=medicos,
        consultorios=consultorios,
        error=error
    )