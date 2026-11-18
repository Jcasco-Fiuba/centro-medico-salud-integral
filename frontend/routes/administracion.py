"""Rutas de administración del centro médico."""

from datetime import datetime
from urllib.parse import urlencode

from flask import Blueprint, redirect, render_template, request, url_for

from services import api_client

administracion_bp = Blueprint("administracion", __name__, url_prefix="/administracion")


@administracion_bp.before_request
def exigir_sesion_admin_backoffice():
    """Exige sesión activa con rol `admin` para operar el módulo de administración."""
    usuario = api_client.obtener_usuario_actual()
    if usuario is None:
        api_client.cerrar_sesion_autenticada()
        destino = api_client.construir_destino_actual(request, url_for("administracion.inicio"))
        return redirect(url_for("auth.iniciar_sesion", next=destino))
    if usuario.get("rol") != "admin":
        return ("No tiene permisos para acceder al módulo de administración.", 403)
    return None


@administracion_bp.get("/")
def inicio():
    """Entrada del backoffice administrativo."""
    return redirect(url_for("administracion.dashboard"))


def obtener_mensaje_error(respuesta, fallback="Ocurrió un error inesperado."):
    """Extrae el mensaje de error de la API (soporta `errores` como lista o `error` como texto)."""
    if isinstance(respuesta, dict):
        errores = respuesta.get("errores")
        if isinstance(errores, list) and errores:
            return str(errores[0])
        error = respuesta.get("error")
        if isinstance(error, str) and error.strip():
            return error.strip()
    return fallback


def _cargar_especialidades():
    """Obtiene la lista completa de especialidades desde la API."""
    respuesta, status = api_client.get("/api/especialidades")
    if status == 200 and isinstance(respuesta, dict):
        lista = respuesta.get("especialidades", [])
        if isinstance(lista, list):
            return lista, None
    return [], obtener_mensaje_error(respuesta, "No se pudieron cargar las especialidades.")


def _cargar_consultorios():
    """Obtiene la lista completa de consultorios desde la API."""
    respuesta, status = api_client.get("/api/consultorios")
    if status == 200 and isinstance(respuesta, dict):
        lista = respuesta.get("consultorios", [])
        if isinstance(lista, list):
            return lista, None
    return [], obtener_mensaje_error(respuesta, "No se pudieron cargar los consultorios.")


def _cargar_medicos():
    """Obtiene el listado base de médicos desde la API."""
    respuesta, status = api_client.get("/api/medicos")
    if status == 200 and isinstance(respuesta, list):
        return respuesta, None
    return [], obtener_mensaje_error(respuesta, "No se pudieron obtener los médicos.")


def cargar_opciones_agenda():
    """Carga médicos y consultorios para formularios y filtros de agendas/turnos."""
    medicos, _ = _cargar_medicos()
    consultorios, _ = _cargar_consultorios()
    return medicos, consultorios


def _formatear_porcentaje(numerador: int, denominador: int) -> str:
    """Formatea un porcentaje con coma decimal (`12,3 %`)."""
    if denominador <= 0:
        return "0,0 %"
    valor = (numerador / denominador) * 100
    return f"{valor:.1f} %".replace(".", ",")


def _calcular_metricas_dashboard(turnos: list[dict]) -> dict:
    """Calcula los indicadores reales del dashboard a partir de los turnos existentes."""
    estados = {
        "disponible": 0,
        "reservado": 0,
        "confirmado": 0,
        "atendido": 0,
        "cancelado": 0,
        "ausente": 0,
    }
    conteo_por_medico: dict[int, int] = {}

    for turno in turnos:
        estado = str(turno.get("estado", "")).lower()
        if estado in estados:
            estados[estado] += 1
        id_medico = turno.get("id_medico")
        if isinstance(id_medico, int):
            conteo_por_medico[id_medico] = conteo_por_medico.get(id_medico, 0) + 1

    total_turnos = len(turnos)
    cupos_ocupados = (
        estados["reservado"] + estados["confirmado"] + estados["atendido"] + estados["ausente"]
    )

    conteo_especialidades: dict[str, int] = {}
    for id_medico, cantidad in conteo_por_medico.items():
        detalle, status_detalle = api_client.get(f"/api/medicos/{id_medico}")
        if status_detalle != 200 or not isinstance(detalle, dict):
            continue
        esps = detalle.get("especialidades") or []
        if not esps:
            conteo_especialidades["Sin especialidad"] = (
                conteo_especialidades.get("Sin especialidad", 0) + cantidad
            )
            continue
        for esp in esps:
            nombre_esp = esp.get("nombre")
            if nombre_esp:
                conteo_especialidades[nombre_esp] = (
                    conteo_especialidades.get(nombre_esp, 0) + cantidad
                )

    max_esp = max(conteo_especialidades.values(), default=0)
    especialidades_ranking = [
        {
            "nombre": nombre,
            "cantidad": cantidad,
            "porcentaje": round((cantidad / max_esp) * 100) if max_esp > 0 else 0,
        }
        for nombre, cantidad in sorted(
            conteo_especialidades.items(), key=lambda item: (-item[1], item[0])
        )[:6]
    ]

    return {
        "total_turnos": total_turnos,
        "ocupacion_porcentaje": _formatear_porcentaje(cupos_ocupados, total_turnos),
        "ocupacion_detalle": f"{cupos_ocupados} de {total_turnos} cupos de agenda",
        "cancelaciones_total": estados["cancelado"],
        "cancelaciones_porcentaje": f"{_formatear_porcentaje(estados['cancelado'], total_turnos)} de los turnos del período",
        "ausentismo_porcentaje": _formatear_porcentaje(estados["ausente"], total_turnos),
        "ausentismo_detalle": f"{estados['ausente']} ausentes de {total_turnos} turnos",
        "total_especialidades": total_turnos,
        "especialidades": especialidades_ranking,
        "estados": estados,
    }


def _filtrar_por_texto_y_estado(items: list[dict], buscar: str, estado: str, campos_texto: tuple[str, ...]) -> list[dict]:
    """Filtra catálogos por coincidencia de texto parcial y estado booleano `activo`."""
    resultado = list(items)
    if buscar:
        termino = buscar.lower()
        resultado = [
            item
            for item in resultado
            if any(termino in str(item.get(campo, "")).lower() for campo in campos_texto)
        ]
    if estado == "activo":
        resultado = [item for item in resultado if item.get("activo") is True]
    elif estado == "inactivo":
        resultado = [item for item in resultado if item.get("activo") is False]
    return resultado


def _extraer_id_especialidad_medico(medico: dict | None) -> int | None:
    """Obtiene el ID de la especialidad principal de un detalle de médico."""
    if not isinstance(medico, dict):
        return None
    if isinstance(medico.get("especialidad_id"), int):
        return medico["especialidad_id"]
    esps = medico.get("especialidades")
    if isinstance(esps, list) and esps and isinstance(esps[0], dict):
        return esps[0].get("id")
    return None


def _cargar_catalogos_formulario_medico(id_consultorio_actual: int | None = None):
    """Carga especialidades y consultorios habilitados (más el actual si está en edición)."""
    especialidades, _ = _cargar_especialidades()
    consultorios, _ = _cargar_consultorios()
    consultorios_filtrados = [
        c
        for c in consultorios
        if c.get("activo") is True or c.get("id") == id_consultorio_actual
    ]
    return especialidades, consultorios_filtrados


def _validar_formulario_medico(form):
    """Valida los campos del formulario de alta/edición de médicos."""
    nombre = form.get("nombre", "").strip()
    apellido = form.get("apellido", "").strip()
    matricula = form.get("matricula", "").strip()
    id_consultorio_raw = form.get("id_consultorio", "").strip()
    especialidad_raw = form.get("especialidad_id", "").strip()

    valores = {
        "nombre": nombre,
        "apellido": apellido,
        "matricula": matricula,
        "id_consultorio": int(id_consultorio_raw) if id_consultorio_raw.isascii() and id_consultorio_raw.isdigit() else id_consultorio_raw,
        "especialidad_id": int(especialidad_raw) if especialidad_raw.isascii() and especialidad_raw.isdigit() else None,
    }

    if not nombre or not apellido or not matricula or not id_consultorio_raw or not especialidad_raw:
        return None, valores, "Nombre, apellido, matrícula, consultorio y especialidad son obligatorios."

    if not (id_consultorio_raw.isascii() and id_consultorio_raw.isdigit()) or int(id_consultorio_raw) <= 0:
        return None, valores, "Seleccioná un consultorio válido."

    if not (especialidad_raw.isascii() and especialidad_raw.isdigit()) or int(especialidad_raw) <= 0:
        return None, valores, "Seleccioná una especialidad válida."

    payload = {
        "nombre": nombre,
        "apellido": apellido,
        "matricula": matricula,
        "id_consultorio": int(id_consultorio_raw),
        "especialidades": [int(especialidad_raw)],
    }
    return payload, valores, None


# --- DASHBOARD ---

@administracion_bp.get("/dashboard")
def dashboard():
    """Panel principal con métricas reales calculadas desde `/api/turnos`."""
    respuesta, status = api_client.get("/api/turnos")
    if status == 200 and isinstance(respuesta, list):
        metricas = _calcular_metricas_dashboard(respuesta)
        error = None
    else:
        metricas = _calcular_metricas_dashboard([])
        error = obtener_mensaje_error(respuesta, "No se pudieron cargar las métricas del dashboard.")

    return render_template("administracion/dashboard.html", metricas=metricas, error=error)


# --- ESPECIALIDADES ---

@administracion_bp.route("/especialidades", methods=["GET"])
def especialidades():
    """Listado con búsqueda y filtro de especialidades médicas."""
    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "")

    lista, error_mensaje = _cargar_especialidades()
    especialidades_data = _filtrar_por_texto_y_estado(lista, buscar, estado, ("nombre",))

    return render_template(
        "administracion/especialidades.html",
        especialidades=especialidades_data,
        buscar=buscar,
        estado=estado,
        error=error_mensaje,
    )


@administracion_bp.route("/especialidades/nueva", methods=["GET", "POST"])
def crear_especialidad():
    """Alta de nueva especialidad médica."""
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
            respuesta, status = api_client.post("/api/especialidades", datos)
            if status in (200, 201):
                return redirect(url_for("administracion.especialidades", creada="1"))
            error = obtener_mensaje_error(respuesta, "No se pudo guardar la especialidad.")

    return render_template(
        "administracion/formulario_especialidad.html",
        editando=False,
        especialidad=None,
        error=error,
    )


@administracion_bp.route("/especialidades/<int:id>/editar", methods=["GET", "POST"])
def editar_especialidad(id):
    """Edición de una especialidad médica existente."""
    error = None

    respuesta_get, status_get = api_client.get(f"/api/especialidades/{id}")
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
            respuesta, status = api_client.patch(f"/api/especialidades/{id}", datos)
            if status in (200, 204):
                return redirect(url_for("administracion.especialidades", editada="1"))
            error = obtener_mensaje_error(respuesta, "No se pudo actualizar la especialidad.")
            especialidad = {"id": id, "nombre": nombre, "descripcion": descripcion}

    return render_template(
        "administracion/formulario_especialidad.html",
        editando=True,
        especialidad=especialidad,
        error=error,
    )


@administracion_bp.route("/especialidades/<int:id>/baja", methods=["POST"])
def dar_baja_especialidad(id):
    """Baja lógica de una especialidad mediante `PATCH /api/especialidades/<id>`."""
    _, status = api_client.patch(f"/api/especialidades/{id}", {"activo": False})
    if status in (200, 204):
        return redirect(url_for("administracion.especialidades", baja="1"))
    return redirect(url_for("administracion.especialidades", error_baja="1"))


# --- MÉDICOS ---

@administracion_bp.route("/medicos", methods=["GET"])
def medicos():
    """Listado de médicos enriquecido con especialidad y consultorio."""
    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "")

    lista_medicos, error_mensaje = _cargar_medicos()
    consultorios, _ = _cargar_consultorios()
    mapa_consultorios = {c.get("id"): c.get("nombre", "") for c in consultorios}

    medicos_filtrados = _filtrar_por_texto_y_estado(
        lista_medicos, buscar, estado, ("nombre", "apellido", "matricula")
    )

    medicos_enriquecidos = []
    for medico in medicos_filtrados:
        item = dict(medico)
        item["consultorio"] = mapa_consultorios.get(medico.get("id_consultorio"), "-")
        detalle, status_det = api_client.get(f"/api/medicos/{medico.get('id')}")
        if status_det == 200 and isinstance(detalle, dict):
            nombres_esp = [e.get("nombre", "") for e in detalle.get("especialidades", []) if e.get("nombre")]
            item["especialidad"] = ", ".join(nombres_esp) if nombres_esp else "-"
        else:
            item["especialidad"] = "-"
        medicos_enriquecidos.append(item)

    return render_template(
        "administracion/medicos.html",
        medicos=medicos_enriquecidos,
        buscar=buscar,
        estado=estado,
        error=error_mensaje,
    )


@administracion_bp.route("/medicos/nuevo", methods=["GET", "POST"])
def nuevo_medico():
    """Alta de un médico alineada con el contrato real de `/api/medicos`."""
    error = None
    medico_form = None
    especialidades_data, consultorios_data = _cargar_catalogos_formulario_medico()

    if request.method == "POST":
        datos, valores, error = _validar_formulario_medico(request.form)
        if error is None and datos is not None:
            respuesta, status = api_client.post("/api/medicos", datos)
            if status in (200, 201):
                return redirect(url_for("administracion.medicos", creada="1"))
            error = obtener_mensaje_error(respuesta, "No se pudo registrar al médico.")
        medico_form = valores

    return render_template(
        "administracion/formulario_medico.html",
        editando=False,
        medico=medico_form,
        especialidades=especialidades_data,
        consultorios=consultorios_data,
        especialidad_seleccionada=_extraer_id_especialidad_medico(medico_form),
        error=error,
    )


@administracion_bp.route("/medicos/<int:id>/editar", methods=["GET", "POST"])
def editar_medico(id):
    """Edición de un médico existente incluyendo consultorio y especialidad."""
    error = None
    respuesta_get, status_get = api_client.get(f"/api/medicos/{id}")
    if status_get != 200 or not isinstance(respuesta_get, dict):
        return redirect(url_for("administracion.medicos", no_encontrado="1"))

    medico = respuesta_get
    especialidades_data, consultorios_data = _cargar_catalogos_formulario_medico(
        medico.get("id_consultorio")
    )

    if request.method == "POST":
        datos, valores, error = _validar_formulario_medico(request.form)
        if error is None and datos is not None:
            respuesta, status = api_client.patch(f"/api/medicos/{id}", datos)
            if status in (200, 204):
                return redirect(url_for("administracion.medicos", editada="1"))
            error = obtener_mensaje_error(respuesta, "No se pudo actualizar el médico.")
        medico = {"id": id, **valores}

    return render_template(
        "administracion/formulario_medico.html",
        editando=True,
        medico=medico,
        especialidades=especialidades_data,
        consultorios=consultorios_data,
        especialidad_seleccionada=_extraer_id_especialidad_medico(medico),
        error=error,
    )


@administracion_bp.route("/medicos/<int:id>/baja", methods=["POST"])
def dar_baja_medico(id):
    """Baja lógica de un médico mediante `PATCH /api/medicos/<id>/baja`."""
    _, status = api_client.patch(f"/api/medicos/{id}/baja")
    if status in (200, 204):
        return redirect(url_for("administracion.medicos", baja="1"))
    return redirect(url_for("administracion.medicos", error_baja="1"))


# --- CONSULTORIOS ---

@administracion_bp.route("/consultorios", methods=["GET"])
def consultorios():
    """Listado principal de consultorios con búsqueda y filtro de estado."""
    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "")

    lista, error_carga = _cargar_consultorios()
    consultorios_list = _filtrar_por_texto_y_estado(
        lista, buscar, estado, ("nombre", "ubicacion")
    )
    error = request.args.get("error") or error_carga

    return render_template(
        "administracion/consultorios.html",
        consultorios=consultorios_list,
        error=error,
    )


@administracion_bp.route("/consultorios/nuevo", methods=["GET", "POST"])
def nuevo_consultorio():
    """Alta de consultorio usando el cliente HTTP autenticado."""
    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "ubicacion": request.form.get("ubicacion", "").strip(),
        }
        respuesta, status = api_client.post("/api/consultorios", datos)
        if status in (200, 201):
            return redirect(url_for("administracion.consultorios"))

        error_msg = obtener_mensaje_error(respuesta, "Error al crear el consultorio.")
        return render_template(
            "administracion/formulario_consultorio.html",
            editando=False,
            error=error_msg,
            consultorio=datos,
        )

    return render_template(
        "administracion/formulario_consultorio.html",
        editando=False,
        consultorio=None,
    )


@administracion_bp.route("/consultorios/<int:id>/editar", methods=["GET", "POST"])
def editar_consultorio(id):
    """Edición de consultorio mediante `PATCH /api/consultorios/<id>`."""
    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "ubicacion": request.form.get("ubicacion", "").strip(),
        }
        respuesta, status = api_client.patch(f"/api/consultorios/{id}", datos)
        if status == 200:
            return redirect(url_for("administracion.consultorios"))

        error_msg = obtener_mensaje_error(respuesta, "Error al actualizar el consultorio.")
        return render_template(
            "administracion/formulario_consultorio.html",
            editando=True,
            consultorio={"id": id, **datos},
            error=error_msg,
        )

    respuesta, status = api_client.get(f"/api/consultorios/{id}")
    if status != 200 or not isinstance(respuesta, dict):
        return redirect(
            url_for(
                "administracion.consultorios",
                error=obtener_mensaje_error(respuesta, "Consultorio no encontrado."),
            )
        )

    consultorio_data = respuesta.get("consultorio")
    return render_template(
        "administracion/formulario_consultorio.html",
        editando=True,
        consultorio=consultorio_data,
    )


@administracion_bp.route("/consultorios/<int:id>/baja", methods=["POST"])
def dar_baja_consultorio(id):
    """Baja lógica de consultorio mediante `PATCH /api/consultorios/<id>/baja`."""
    respuesta, status = api_client.patch(f"/api/consultorios/{id}/baja")
    if status == 200:
        return redirect(url_for("administracion.consultorios"))

    error_msg = obtener_mensaje_error(respuesta, "No se pudo dar de baja el consultorio.")
    return redirect(url_for("administracion.consultorios", error=error_msg))


# --- AGENDAS Y TURNOS ---

@administracion_bp.route("/agendas")
def agendas():
    """Listado general de turnos con filtros por médico y estado."""
    medico = request.args.get("medico", "")
    estado = request.args.get("estado", "")

    filtros = {}
    if medico:
        filtros["medico"] = medico
    if estado:
        filtros["estado"] = estado

    ruta = "/api/turnos"
    if filtros:
        ruta = f"{ruta}?{urlencode(filtros)}"

    respuesta, status = api_client.get(ruta)
    medicos_list, error_medicos_msg = _cargar_medicos()
    consultorios_list, _ = _cargar_consultorios()
    mapa_medicos = {
        m.get("id"): f"{m.get('nombre', '')} {m.get('apellido', '')}".strip()
        for m in medicos_list
    }
    mapa_consultorios = {c.get("id"): c.get("nombre", "") for c in consultorios_list}

    error = None
    turnos = []
    if status == 200 and isinstance(respuesta, list):
        for t in respuesta:
            item = dict(t)
            item["medico_nombre"] = mapa_medicos.get(t.get("id_medico"), str(t.get("id_medico", "")))
            item["consultorio_nombre"] = mapa_consultorios.get(
                t.get("id_consultorio"), str(t.get("id_consultorio", ""))
            )
            turnos.append(item)
    else:
        error = obtener_mensaje_error(respuesta, "No se pudieron cargar los turnos.")

    error_medicos = "No se pudieron cargar los médicos." if error_medicos_msg else None

    return render_template(
        "administracion/agendas.html",
        medico=medico,
        estado=estado,
        turnos=turnos,
        error=error,
        medicos=medicos_list,
        error_medicos=error_medicos,
    )


@administracion_bp.route("/agendas/disponibilidad")
def disponibilidad():
    """Consulta pública de disponibilidad por médico y fecha."""
    medico = request.args.get("medico", "")
    fecha = request.args.get("fecha", "")

    turnos = []
    error = None

    if medico and fecha:
        ruta = "/api/turnos/disponibles?" + urlencode({"medico": medico, "fecha": fecha})
        respuesta, status = api_client.get(ruta)
        if status == 200 and isinstance(respuesta, list):
            turnos = respuesta
        else:
            error = obtener_mensaje_error(respuesta, "No se pudo consultar la disponibilidad.")

    medicos_list, _ = cargar_opciones_agenda()

    return render_template(
        "administracion/disponibilidad.html",
        medico=medico,
        fecha=fecha,
        turnos=turnos,
        medicos=medicos_list,
        error=error,
    )


@administracion_bp.get("/turnos/nuevo")
def nuevo_turno():
    """Formulario para habilitar un turno disponible."""
    medicos_list, consultorios_list = cargar_opciones_agenda()
    return render_template(
        "administracion/crear_turno.html",
        medicos=medicos_list,
        consultorios=consultorios_list,
        error=None,
    )


@administracion_bp.post("/turnos/nuevo")
def guardar_turno():
    """Crea un turno disponible en la API."""
    medico = request.form.get("medico", "").strip()
    consultorio = request.form.get("consultorio", "").strip()
    fecha = request.form.get("fecha", "").strip()
    hora = request.form.get("hora", "").strip()

    error = None
    if (
        not (medico.isascii() and medico.isdigit())
        or not (consultorio.isascii() and consultorio.isdigit())
        or not fecha
        or not hora
    ):
        error = "Completá correctamente todos los campos."
    elif int(medico) <= 0 or int(consultorio) <= 0:
        error = "Seleccioná un médico y un consultorio válidos."
    else:
        try:
            fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            datos = {
                "id_medico": int(medico),
                "id_consultorio": int(consultorio),
                "fecha_hora": fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
            }
            respuesta, status = api_client.post("/api/turnos", datos)
            if status == 201:
                return redirect(url_for("administracion.agendas", creado="1"))
            error = obtener_mensaje_error(respuesta, "No se pudo crear el turno.")
        except ValueError:
            error = "La fecha o la hora ingresadas no son válidas."

    medicos_list, consultorios_list = cargar_opciones_agenda()
    return render_template(
        "administracion/crear_turno.html",
        medicos=medicos_list,
        consultorios=consultorios_list,
        error=error,
    )
