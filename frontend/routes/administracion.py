"""Rutas de administración del centro médico."""

from datetime import datetime
from urllib.parse import urlencode

from flask import Blueprint, redirect, render_template, request, url_for
from services import api_client

administracion_bp = Blueprint("administracion", __name__, url_prefix="/administracion")


# --- HELPER PARA MANEJO DE ERRORES DE LA API ---

def obtener_mensaje_error(respuesta, fallback="Ocurrió un error inesperado."):
    """Extrae el mensaje de error de la API (soporta clave 'errores' como lista o 'error' como texto)."""
    if isinstance(respuesta, dict):
        if "errores" in respuesta and isinstance(respuesta["errores"], list) and respuesta["errores"]:
            return respuesta["errores"][0]
        if "error" in respuesta:
            return respuesta["error"]
    return fallback


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


# --- DASHBOARD ---

@administracion_bp.get("/dashboard")
def dashboard():
    respuesta, status = api_client.get("/api/dashboard/stats")

    if status == 200 and isinstance(respuesta, dict) and "total_turnos" in respuesta:
        metricas = respuesta
    else:
        metricas = {
            "total_turnos": 64,
            "ocupacion_porcentaje": "72,5 %",
            "ocupacion_detalle": "58 de 80 cupos de agenda",
            "cancelaciones_total": 6,
            "cancelaciones_porcentaje": "9,4 % de los turnos del día",
            "ausentismo_porcentaje": "6,3 %",
            "ausentismo_detalle": "4 ausentes de 64 turnos",
            "total_especialidades": 64,
            "especialidades": [
                {"nombre": "Clínica médica", "cantidad": 22, "porcentaje": 100},
                {"nombre": "Cardiología", "cantidad": 16, "porcentaje": 73},
                {"nombre": "Dermatología", "cantidad": 10, "porcentaje": 45},
                {"nombre": "Traumatología", "cantidad": 8, "porcentaje": 36},
                {"nombre": "Ginecología", "cantidad": 5, "porcentaje": 23},
                {"nombre": "Pediatría", "cantidad": 3, "porcentaje": 14},
            ],
            "estados": {
                "reservado": 40,
                "confirmado": 5,
                "atendido": 9,
                "cancelado": 6,
                "ausente": 4,
            },
        }

    return render_template("administracion/dashboard.html", metricas=metricas)


# --- ESPECIALIDADES ---

@administracion_bp.route("/especialidades", methods=["GET"])
def especialidades():
    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "")
    error_mensaje = None
    especialidades_data = []

    try:
        respuesta, status = api_client.get("/api/especialidades")

        if status == 200 and isinstance(respuesta, dict) and "especialidades" in respuesta:
            lista = respuesta["especialidades"]

            if buscar:
                lista = [e for e in lista if buscar.lower() in e.get("nombre", "").lower()]

            if estado == "activo":
                lista = [e for e in lista if e.get("activo") is True]
            elif estado == "inactivo":
                lista = [e for e in lista if e.get("activo") is False]

            especialidades_data = lista
        else:
            error_mensaje = obtener_mensaje_error(respuesta, "No se pudieron obtener las especialidades.")
    except Exception:
        error_mensaje = "Error de conexión con el servicio backend."

    return render_template(
        "administracion/especialidades.html",
        especialidades=especialidades_data,
        buscar=buscar,
        estado=estado,
        error=error_mensaje,
    )


@administracion_bp.route("/especialidades/nueva", methods=["GET", "POST"])
def crear_especialidad():
    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        if not nombre:
            error = "El nombre de la especialidad es obligatorio."
        elif len(nombre) < 3:
            error = "El nombre debe tener al menos 3 caracteres."
        elif len(nombre) > 50:
            error = "El nombre no puede superar los 50 caracteres."
        else:
            datos = {"nombre": nombre, "descripcion": descripcion}
            try:
                respuesta, status = api_client.post("/api/especialidades", datos)

                if status in (200, 201):
                    return redirect(url_for("administracion.especialidades", creada="1"))

                error = obtener_mensaje_error(respuesta, "No se pudo guardar la especialidad.")
            except Exception:
                error = "Error crítico de conexión al intentar crear la especialidad."

    return render_template(
        "administracion/formulario_especialidad.html",
        editando=False,
        especialidad=None,
        error=error,
    )


@administracion_bp.route("/especialidades/<int:id>/editar", methods=["GET", "POST"])
def editar_especialidad(id):
    error = None

    try:
        respuesta_get, status_get = api_client.get(f"/api/especialidades/{id}")
    except Exception:
        return redirect(url_for("administracion.especialidades", error_conexion="1"))

    if status_get != 200 or not isinstance(respuesta_get, dict):
        return redirect(url_for("administracion.especialidades", no_encontrado="1"))

    especialidad = respuesta_get

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        if not nombre:
            error = "El nombre de la especialidad es obligatorio."
        elif len(nombre) < 3:
            error = "El nombre debe tener al menos 3 caracteres."
        elif len(nombre) > 50:
            error = "El nombre no puede superar los 50 caracteres."
        else:
            datos = {"nombre": nombre, "descripcion": descripcion}
            try:
                respuesta, status = api_client.patch(f"/api/especialidades/{id}", datos)

                if status in (200, 204):
                    return redirect(url_for("administracion.especialidades", editada="1"))

                error = obtener_mensaje_error(respuesta, "No se pudo actualizar la especialidad.")
            except Exception:
                error = "Error de conexión al actualizar la especialidad."

    return render_template(
        "administracion/formulario_especialidad.html",
        editando=True,
        especialidad=especialidad,
        error=error,
    )


@administracion_bp.route("/especialidades/<int:id>/baja", methods=["POST"])
def dar_baja_especialidad(id):
    try:
        respuesta, status = api_client.patch(f"/api/especialidades/{id}", {"activo": False})
        if status in (200, 204):
            return redirect(url_for("administracion.especialidades", baja="1"))
    except Exception:
        pass

    return redirect(url_for("administracion.especialidades", error_baja="1"))


# --- MEDICOS ---

@administracion_bp.route("/medicos", methods=["GET"])
def medicos():
    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "")
    error_mensaje = None
    medicos_data = []

    try:
        respuesta, status = api_client.get("/api/medicos")

        if status == 200 and isinstance(respuesta, list):
            lista = respuesta

            if buscar:
                b = buscar.lower()
                lista = [
                    m for m in lista 
                    if b in m.get("nombre", "").lower() 
                    or b in m.get("apellido", "").lower()
                    or b in str(m.get("matricula", "")).lower()
                ]

            if estado == "activo":
                lista = [m for m in lista if m.get("activo") is True]
            elif estado == "inactivo":
                lista = [m for m in lista if m.get("activo") is False]

            medicos_data = lista
        else:
            error_mensaje = obtener_mensaje_error(respuesta, "No se pudieron obtener los médicos.")
    except Exception:
        error_mensaje = "Error de conexión con el servicio backend."

    return render_template(
        "administracion/medicos.html",
        medicos=medicos_data,
        buscar=buscar,
        estado=estado,
        error=error_mensaje,
    )


@administracion_bp.route("/medicos/nuevo", methods=["GET", "POST"])
def nuevo_medico():
    error = None
    especialidades_data = []

    
    # Cargar especialidades para el desplegable del formulario
    try:
        resp_esp, status_esp = api_client.get("/api/especialidades")
        if status_esp == 200 and isinstance(resp_esp, dict) and "especialidades" in resp_esp:
            especialidades_data = resp_esp["especialidades"]
    except Exception:
        pass

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        matricula = request.form.get("matricula", "").strip()
        especialidad_id = request.form.get("especialidad_id", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()

        if not nombre or not apellido or not matricula or not especialidad_id:
            error = "Nombre, apellido, matrícula y especialidad son obligatorios."
        else:
            datos = {
                "nombre": nombre,
                "apellido": apellido,
                "matricula": matricula,
                "email": email,
                "telefono": telefono,
                "especialidades": [int(especialidad_id)]
            }
            try:
                respuesta, status = api_client.post("/api/medicos", datos)
                if status in (200, 201):
                    return redirect(url_for("administracion.medicos", creada="1"))

                error = obtener_mensaje_error(respuesta, "No se pudo registrar al médico.")
            except Exception:
                error = "Error de conexión al intentar crear el médico."

    return render_template(
        "administracion/formulario_medico.html",
        editando=False,
        medico=None,
        especialidades=especialidades_data,
        error=error,
    )


@administracion_bp.route("/medicos/<int:id>/editar", methods=["GET", "POST"])
def editar_medico(id):
    error = None
    medico = None
    especialidades_data = []

    try:
        resp_esp, status_esp = api_client.get("/api/especialidades")
        if status_esp == 200 and isinstance(resp_esp, dict) and "especialidades" in resp_esp:
            especialidades_data = resp_esp["especialidades"]
    except Exception:
        pass

    try:
        respuesta_get, status_get = api_client.get(f"/api/medicos/{id}")
        if status_get == 200 and isinstance(respuesta_get, dict):
            medico = respuesta_get
        else:
            return redirect(url_for("administracion.medicos", no_encontrado="1"))
    except Exception:
        return redirect(url_for("administracion.medicos", error_conexion="1"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        matricula = request.form.get("matricula", "").strip()
        especialidad_id = request.form.get("especialidad_id", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()

        if not nombre or not apellido or not matricula or not especialidad_id:
            error = "Nombre, apellido, matrícula y especialidad son obligatorios."
        else:
            datos = {
                "nombre": nombre,
                "apellido": apellido,
                "matricula": matricula,
                "email": email,
                "telefono": telefono,
                "especialidades": [int(especialidad_id)]
            }
            try:
                respuesta, status = api_client.patch(f"/api/medicos/{id}", datos)
                if status in (200, 204):
                    return redirect(url_for("administracion.medicos", editada="1"))

                error = obtener_mensaje_error(respuesta, "No se pudo actualizar el médico.")
            except Exception:
                error = "Error de conexión al actualizar los datos del médico."

    return render_template(
        "administracion/formulario_medico.html",
        editando=True,
        medico=medico,
        especialidades=especialidades_data,
        error=error,
    )


@administracion_bp.route("/medicos/<int:id>/baja", methods=["POST"])
def dar_baja_medico(id):
    try:
        respuesta, status = api_client.patch(f"/api/medicos/{id}/baja", {})
        if status in (200, 204):
            return redirect(url_for("administracion.medicos", baja="1"))
    except Exception:
        pass

    return redirect(url_for("administracion.medicos", error_baja="1"))


# --- CONSULTORIOS ---

@administracion_bp.route("/consultorios", methods=["GET"])
def consultorios():
    """Listado principal de consultorios."""
    try:
        res = api_client.get("/api/consultorios")
        consultorios_list = res.json().get("consultorios", []) if res.status_code == 200 else []
    except Exception:
        consultorios_list = []
        
    error = request.args.get("error")
    return render_template("administracion/consultorios.html", consultorios=consultorios_list, error=error)


@administracion_bp.route("/consultorios/nuevo", methods=["GET", "POST"])
def nuevo_consultorio():
    """Alta de consultorio."""
    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre"),
            "ubicacion": request.form.get("ubicacion")
        }
        
        res = api_client.post("/api/consultorios", json=datos)
        if res.status_code in (200, 201):
            return redirect(url_for("administracion.consultorios"))
            
        body = res.json()
        error_msg = body.get("errores", [body.get("error", "Error al crear el consultorio")])[0]
        return render_template("administracion/formulario_consultorio.html", editando=False, error=error_msg, consultorio=datos)

    return render_template("administracion/formulario_consultorio.html", editando=False, consultorio=None)


@administracion_bp.route("/consultorios/<int:id>/editar", methods=["GET", "POST"])
def editar_consultorio(id):
    """Edición de consultorio (Usa PATCH hacia el Backend)."""
    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre"),
            "ubicacion": request.form.get("ubicacion")
        }
        
        res = api_client.patch(f"/api/consultorios/{id}", json=datos)
        if res.status_code == 200:
            return redirect(url_for("administracion.consultorios"))
            
        body = res.json()
        error_msg = body.get("errores", [body.get("error", "Error al actualizar")])[0]
        return render_template("administracion/formulario_consultorio.html", editando=True, consultorio=datos, error=error_msg)

    res = api_client.get(f"/api/consultorios/{id}")
    consultorio_data = res.json().get("consultorio") if res.status_code == 200 else None

    return render_template("administracion/formulario_consultorio.html", editando=True, consultorio=consultorio_data)


@administracion_bp.route("/consultorios/<int:id>/baja", methods=["POST"])
def dar_baja_consultorio(id):
    """Baja lógica de consultorio."""
    res = api_client.patch(f"/api/consultorios/{id}/baja")
    if res.status_code == 200:
        return redirect(url_for("administracion.consultorios"))
        
    error_msg = res.json().get("error", "No se pudo dar de baja el consultorio.")
    return redirect(url_for("administracion.consultorios", error=error_msg))

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