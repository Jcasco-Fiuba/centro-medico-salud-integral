"""Rutas del portal autenticado de paciente"""
import calendar
from datetime import date, datetime, timedelta

import requests
from flask import Blueprint, redirect, render_template, request, session, url_for


paciente_bp = Blueprint("paciente", __name__, url_prefix="/paciente")

API_URL = "http://127.0.0.1:5000/api"
 
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGOS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
                "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

 
# Regla del TP (docs/alcance_y_endpoints.md): todos los turnos duran 30 minutos
DURACION_TURNO = 30
 
 
@paciente_bp.route("/")
def portal():
    """Portal del paciente: trae sus datos y su próximo turno desde el backend."""
    ahora = datetime.now()
    hoy = f"{DIAS[ahora.weekday()]} {ahora.day} {MESES[ahora.month - 1]} {ahora.year}"
 
    # cuando esté el login, él guarda estos datos en la sesión.
    id_usuario = session.get("id_usuario", 1)
    dni = session.get("dni", "99999999")
 
    try:
        #1 Datos del paciente
        respuesta = requests.get(f"{API_URL}/pacientes/{dni}", timeout=5)
        if respuesta.status_code != 200:
            return render_template("paciente/portal.html", hoy=hoy, paciente=None,
                                   proximo_turno=None, error="No encontramos tus datos de paciente.")
        paciente = respuesta.json()["paciente"]
        paciente["iniciales"] = paciente["nombre"][0] + paciente["apellido"][0]
 
        #2 Todos los turnos #-> falta filtra por paciente en el back
        turnos = requests.get(f"{API_URL}/turnos", timeout=5).json()
 
        #3 Buscamos el turno más cercano de este paciente que todavía no pasó
        turno_elegido = None
        fecha_elegida = None
        for turno in turnos:
            # La API manda las fechas así: "Wed, 18 Nov 2026 10:30:00 GMT"
            fecha = datetime.strptime(turno["fecha_hora"], "%a, %d %b %Y %H:%M:%S GMT")
            es_mio = turno["id_usuario"] == id_usuario
            esta_activo = turno["estado"] in ["reservado", "confirmado"]
            if es_mio and esta_activo and fecha >= ahora:
                if fecha_elegida is None or fecha < fecha_elegida:
                    turno_elegido = turno
                    fecha_elegida = fecha
 
        # 4 Si hay turno, buscamos el médico y el consultorio para mostrar los nombres
        proximo_turno = None
        if turno_elegido is not None:
            medico = requests.get(f"{API_URL}/medicos/{turno_elegido['id_medico']}", timeout=5).json()
            consultorio = requests.get(f"{API_URL}/consultorios/{turno_elegido['id_consultorio']}", timeout=5).json()["consultorio"]
 
            especialidades = []
            for especialidad in medico.get("especialidades", []):
                especialidades.append(especialidad["nombre"])
 
            desde = fecha_elegida - timedelta(minutes=15)
            hasta = fecha_elegida + timedelta(minutes=15)
            limite_cancelar = fecha_elegida - timedelta(hours=24)
 
            proximo_turno = {
                "id": turno_elegido["id"],
                "codigo": f"Turno N.º {turno_elegido['id']}",
                "estado": turno_elegido["estado"],
                "especialidad": ", ".join(especialidades),
                "medico": f"{medico['nombre']} {medico['apellido']}",
                "fecha": f"{DIAS[fecha_elegida.weekday()]} {fecha_elegida.strftime('%d/%m/%Y')}",
                "hora": fecha_elegida.strftime("%H:%M"),
                "duracion": DURACION_TURNO,
                "consultorio": f"{consultorio['nombre']} · {consultorio['ubicacion']}",
                "texto_checkin": f"El {fecha_elegida.strftime('%d/%m')} podés registrar tu llegada entre las "
                                 f"{desde.strftime('%H:%M')} y las {hasta.strftime('%H:%M')} h inclusive. "
                                 f"Llegá a las {desde.strftime('%H:%M')} h con tu DNI.",
                "cancelar_hasta": limite_cancelar.strftime("%d/%m a las %H:%M h"),
            }
 
    except requests.exceptions.RequestException:
        return render_template("paciente/portal.html", hoy=hoy, paciente=None,
                               proximo_turno=None, error="No se pudo conectar con el servidor.")
 
    return render_template("paciente/portal.html", hoy=hoy, paciente=paciente
                           ,
                           proximo_turno=proximo_turno, error=None)

@paciente_bp.route("/reservar/especialidad")
def elegir_especialidad():
    """Paso 1 de la reserva: muestra las especialidades para elegir una."""
    # Lo que la persona escribió en el buscador (si no escribió nada, queda " ")
    busqueda = request.args.get("busqueda", "")
    # La especialidad ya elegida, si vuelve desde el paso 2
    especialidad_id = request.args.get("especialidad", type=int)
 
    dni = session.get("dni", "99999999")
 
    try:
        #1  Datos del paciente, para la navbar y el resumen
        respuesta = requests.get(f"{API_URL}/pacientes/{dni}", timeout=5)
        paciente = respuesta.json()["paciente"]
        paciente["iniciales"] = paciente["nombre"][0] + paciente["apellido"][0]
 
        #2 Todas las especialidades
        respuesta = requests.get(f"{API_URL}/especialidades", timeout=5)
        if respuesta.status_code != 200:
            return render_template("paciente/especialidad.html", paciente=paciente, especialidades=[],
                                   busqueda=busqueda, especialidad=None,
                                   error="No pudimos cargar las especialidades.")
        todas = respuesta.json()["especialidades"]
 
    except requests.exceptions.RequestException:
        return render_template("paciente/especialidad.html", paciente=None, especialidades=[],
                               busqueda=busqueda, especialidad=None,
                               error="No se pudo conectar con el servidor.")
 
    #3 Nos quedamos con las que coinciden con la búsqueda
    #    y buscamos la que ya estaba elegida (si hay)
    especialidades = []
    especialidad = None
    for item in todas:
        if busqueda.lower() in item["nombre"].lower():
            especialidades.append(item)
        if item["id"] == especialidad_id:
            especialidad = item
 
    return render_template("paciente/especialidad.html", paciente=paciente, especialidades=especialidades,
                           busqueda=busqueda, especialidad=especialidad, error=None)
 
 
@paciente_bp.route("/reservar/profesional")
def elegir_profesional():
    """Paso 2 de la reserva: muestra los médicos de la especialidad elegida."""
    especialidad_id = request.args.get("especialidad", type=int)
    medico_id = request.args.get("medico", type=int)   # si vuelve desde el paso 3
    busqueda = request.args.get("busqueda", "")
 
    # Si no eligió especialidad, lo mandamos al paso 1
    if especialidad_id is None:
        return redirect(url_for("paciente.elegir_especialidad"))
 
    dni = session.get("dni", "99999999")
    ahora = datetime.now()
 
    try:
        #1 Datos del paciente, para la navbar y el resumen
        paciente = requests.get(f"{API_URL}/pacientes/{dni}", timeout=5).json()["paciente"]
        paciente["iniciales"] = paciente["nombre"][0] + paciente["apellido"][0]
 
        #2 Todos los médicos
        todos = requests.get(f"{API_URL}/medicos", timeout=5).json()
 
        medicos = []
        especialidad = None
        medico_elegido = None
        for medico in todos:
            nombre_completo = medico["nombre"] + " " + medico["apellido"]
            if not medico["activo"] or busqueda.lower() not in nombre_completo.lower():
                continue
 
            #3 El detalle del médico trae sus especialidades:
            #-> nos quedamos solo con los que tienen la especialidad elegida
            detalle = requests.get(f"{API_URL}/medicos/{medico['id']}", timeout=5).json()
            tiene_especialidad = False
            for item in detalle["especialidades"]:
                if item["id"] == especialidad_id:
                    tiene_especialidad = True
                    especialidad = item
            if not tiene_especialidad:
                continue
 
            #4 Su próximo turno disponible (el más cercano que todavía no pasó)
            turnos = requests.get(f"{API_URL}/turnos?medico={medico['id']}&estado=disponible", timeout=5).json()
            proxima_fecha = None
            for turno in turnos:
                fecha = datetime.strptime(turno["fecha_hora"], "%a, %d %b %Y %H:%M:%S GMT")
                if fecha >= ahora and (proxima_fecha is None or fecha < proxima_fecha):
                    proxima_fecha = fecha
 
            medico["nombre_completo"] = nombre_completo
            medico["iniciales"] = medico["nombre"][0] + medico["apellido"][0]
            if proxima_fecha is None:
                medico["proximo"] = None
            else:
                medico["proximo"] = (f"{DIAS[proxima_fecha.weekday()][:3]} {proxima_fecha.day} "
                                     f"{MESES[proxima_fecha.month - 1]} · desde las {proxima_fecha.strftime('%H:%M')} h")
            medicos.append(medico)
 
            if medico["id"] == medico_id:
                medico_elegido = medico
 
    except requests.exceptions.RequestException:
        return render_template("paciente/profesional.html", paciente=None, medicos=[], busqueda=busqueda,
                               especialidad_id=especialidad_id, especialidad=None, medico=None,
                               error="No se pudo conectar con el servidor.")
 
    return render_template("paciente/profesional.html", paciente=paciente, medicos=medicos, busqueda=busqueda,
                           especialidad_id=especialidad_id, especialidad=especialidad, medico=medico_elegido,
                           error=None)
def leer_fecha(texto):
    """Convierte la fecha que manda la API ("Wed, 18 Nov 2026 10:30:00 GMT") en datetime."""
    return datetime.strptime(texto, "%a, %d %b %Y %H:%M:%S GMT")


@paciente_bp.route("/reservar/fecha")
def elegir_fecha():
    """Paso 3 de la reserva: calendario del mes y horarios libres del día elegido."""
    especialidad_id = request.args.get("especialidad", type=int)
    medico_id = request.args.get("medico", type=int)
    mes_texto = request.args.get("mes", "")        # "AAAA-MM", el mes que se está mirando
    fecha_texto = request.args.get("fecha", "")    # "AAAA-MM-DD", el día elegido

    if especialidad_id is None or medico_id is None:
        return redirect(url_for("paciente.elegir_especialidad"))

    dni = session.get("dni", "99999999")
    hoy = date.today()

    # Día elegido (si hay) y mes a mostrar
    dia_elegido = None
    if fecha_texto != "":
        dia_elegido = datetime.strptime(fecha_texto, "%Y-%m-%d").date()

    if mes_texto != "":
        anio, mes = int(mes_texto[:4]), int(mes_texto[5:])
    elif dia_elegido is not None:
        anio, mes = dia_elegido.year, dia_elegido.month
    else:
        anio, mes = hoy.year, hoy.month

    try:
        # 1) Paciente, médico, especialidad y consultorio
        paciente = requests.get(f"{API_URL}/pacientes/{dni}", timeout=5).json()["paciente"]
        paciente["iniciales"] = paciente["nombre"][0] + paciente["apellido"][0]

        medico = requests.get(f"{API_URL}/medicos/{medico_id}", timeout=5).json()
        medico["nombre_completo"] = medico["nombre"] + " " + medico["apellido"]

        especialidad = {"nombre": ""}
        for item in medico.get("especialidades", []):
            if item["id"] == especialidad_id:
                especialidad = item

        consultorio = requests.get(f"{API_URL}/consultorios/{medico['id_consultorio']}", timeout=5).json()["consultorio"]

        # 2) Todos los turnos libres del médico (para marcar los días en el calendario)
        turnos = requests.get(f"{API_URL}/turnos?medico={medico_id}&estado=disponible", timeout=5).json()

        # 3) Los turnos libres del día elegido (el backend ya los devuelve ordenados por hora)
        turnos_del_dia = []
        if dia_elegido is not None:
            turnos_del_dia = requests.get(f"{API_URL}/turnos/disponibles?medico={medico_id}&fecha={fecha_texto}", timeout=5).json()

    except requests.exceptions.RequestException:
        return redirect(url_for("paciente.elegir_profesional", especialidad=especialidad_id, medico=medico_id))

    ahora = datetime.now()

    # Días que tienen algún turno libre que todavía no pasó
    dias_disponibles = []
    for turno in turnos:
        fecha_hora = leer_fecha(turno["fecha_hora"])
        if fecha_hora >= ahora:
            dias_disponibles.append(fecha_hora.date())

    # Horarios del día elegido que todavía no pasaron
    horarios = []
    for turno in turnos_del_dia:
        fecha_hora = leer_fecha(turno["fecha_hora"])
        if fecha_hora >= ahora:
            horarios.append({"id": turno["id"], "hora": fecha_hora.strftime("%H:%M")})

    # 4) Armamos el calendario: una lista de semanas, cada semana con 7 días (None = casillero vacío)
    semanas = []
    for semana in calendar.monthcalendar(anio, mes):
        dias = []
        for numero in semana:
            if numero == 0:
                dias.append(None)
            else:
                dia = date(anio, mes, numero)
                dias.append({
                    "dia": numero,
                    "iso": dia.isoformat(),
                    "pasado": dia < hoy,
                    "disponible": dia in dias_disponibles,
                    "seleccionado": dia == dia_elegido,
                })
        semanas.append(dias)

    # 5) Mes anterior (solo si no es un mes que ya pasó) y mes siguiente, en formato "AAAA-MM"
    if mes == 1:
        anterior = date(anio - 1, 12, 1)
    else:
        anterior = date(anio, mes - 1, 1)
    if mes == 12:
        siguiente = date(anio + 1, 1, 1)
    else:
        siguiente = date(anio, mes + 1, 1)

    mes_anterior = None
    if anterior >= date(hoy.year, hoy.month, 1):
        mes_anterior = anterior.strftime("%Y-%m")

    # 6) Textos del día elegido
    fecha = None
    if dia_elegido is not None:
        fecha = {
            "titulo": f"{DIAS[dia_elegido.weekday()]} {dia_elegido.day}",
            "subtitulo": f"{MESES_LARGOS[dia_elegido.month - 1]} de {dia_elegido.year} · Duración estimada: {DURACION_TURNO} minutos",
            "corta": dia_elegido.strftime("%d/%m"),
        }

    return render_template(
        "paciente/elegir_fecha.html",
        paciente=paciente,
        especialidad=especialidad,
        especialidad_id=especialidad_id,
        medico=medico,
        medico_id=medico_id,
        consultorio=consultorio["nombre"],
        mes=f"{anio}-{mes:02d}",
        mes_titulo=f"{MESES_LARGOS[mes - 1]} {anio}",
        mes_anterior=mes_anterior,
        mes_siguiente=siguiente.strftime("%Y-%m"),
        semanas=semanas,
        hoy_texto=hoy.strftime("%d/%m/%Y"),
        fecha=fecha,
        fecha_pasada=dia_elegido is not None and dia_elegido < hoy,
        horarios=horarios,
        error=None,
    )


@paciente_bp.route("/reservar/confirmar", methods=["GET", "POST"])
def confirmar_reserva():
    """Paso 4 de la reserva.
    GET: muestra el resumen del turno elegido.
    POST: le pide al backend que lo reserve y, si sale bien, muestra el comprobante.
    """
    if request.method == "POST":
        turno_id = request.form.get("turno", type=int)
        especialidad_id = request.form.get("especialidad", type=int)
    else:
        turno_id = request.args.get("turno", type=int)
        especialidad_id = request.args.get("especialidad", type=int)

    if turno_id is None:
        return redirect(url_for("paciente.elegir_especialidad"))

    id_usuario = session.get("id_usuario", 1)
    dni = session.get("dni", "99999999")
    problema = None

    try:
        # Si confirmó (POST), primero intentamos reservar
        if request.method == "POST":
            respuesta = requests.post(f"{API_URL}/turnos/reservar", json={"turno_id": turno_id}, timeout=5)
            if respuesta.status_code == 200:
                return redirect(url_for("paciente.turno_reservado", turno_id=turno_id))
            problema = "error"

        # Datos para mostrar el resumen
        paciente = requests.get(f"{API_URL}/pacientes/{dni}", timeout=5).json()["paciente"]
        paciente["iniciales"] = paciente["nombre"][0] + paciente["apellido"][0]

        respuesta = requests.get(f"{API_URL}/turnos/{turno_id}", timeout=5)
        if respuesta.status_code != 200:
            return redirect(url_for("paciente.elegir_especialidad"))
        turno = respuesta.json()

        medico = requests.get(f"{API_URL}/medicos/{turno['id_medico']}", timeout=5).json()
        consultorio = requests.get(f"{API_URL}/consultorios/{turno['id_consultorio']}", timeout=5).json()["consultorio"]

    except requests.exceptions.RequestException:
        return redirect(url_for("paciente.portal"))

    # Si el turno ya no está libre: o es mío (duplicado) o lo tomó otra persona (ocupado)
    if turno["estado"] != "disponible":
        if turno["id_usuario"] == id_usuario:
            problema = "duplicado"
        else:
            problema = "ocupado"

    especialidad_nombre = ""
    for item in medico.get("especialidades", []):
        if item["id"] == especialidad_id:
            especialidad_nombre = item["nombre"]

    fecha_hora = leer_fecha(turno["fecha_hora"])
    datos_turno = {
        "id": turno["id"],
        "id_medico": turno["id_medico"],
        "codigo": f"Turno N.º {turno['id']}",
        "medico": medico["nombre"] + " " + medico["apellido"],
        "fecha_dmy": fecha_hora.strftime("%d/%m/%Y"),
        "hora": fecha_hora.strftime("%H:%M"),
        "sede": consultorio["ubicacion"],
        "consultorio_nombre": consultorio["nombre"],
    }

    return render_template(
        "paciente/confirmar_reserva.html",
        paciente=paciente,
        turno=datos_turno,
        especialidad_id=especialidad_id,
        especialidad_nombre=especialidad_nombre,
        problema=problema,
    )


@paciente_bp.route("/reservar/listo/<int:turno_id>")
def turno_reservado(turno_id):
    """Pantalla final: turno reservado correctamente, con el comprobante."""
    id_usuario = session.get("id_usuario", 1)
    dni = session.get("dni", "99999999")

    try:
        paciente = requests.get(f"{API_URL}/pacientes/{dni}", timeout=5).json()["paciente"]
        paciente["iniciales"] = paciente["nombre"][0] + paciente["apellido"][0]

        respuesta = requests.get(f"{API_URL}/turnos/{turno_id}", timeout=5)
        if respuesta.status_code != 200:
            return redirect(url_for("paciente.portal"))
        turno = respuesta.json()

        # Solo se muestra si el turno es de este paciente
        if turno["id_usuario"] != id_usuario:
            return redirect(url_for("paciente.portal"))

        medico = requests.get(f"{API_URL}/medicos/{turno['id_medico']}", timeout=5).json()
        consultorio = requests.get(f"{API_URL}/consultorios/{turno['id_consultorio']}", timeout=5).json()["consultorio"]

    except requests.exceptions.RequestException:
        return redirect(url_for("paciente.portal"))

    especialidades = []
    for item in medico.get("especialidades", []):
        especialidades.append(item["nombre"])

    fecha_hora = leer_fecha(turno["fecha_hora"])
    llegada = fecha_hora - timedelta(minutes=15)
    limite_cancelar = fecha_hora - timedelta(hours=24)

    datos_turno = {
        "codigo": f"Turno N.º {turno['id']}",
        "token": turno.get("string_token"),
        "emitido": date.today().strftime("%d/%m/%Y"),
        "especialidad": ", ".join(especialidades),
        "medico": medico["nombre"] + " " + medico["apellido"],
        "fecha": f"{DIAS[fecha_hora.weekday()]} {fecha_hora.day} de {MESES_LARGOS[fecha_hora.month - 1].lower()} de {fecha_hora.year}",
        "hora": fecha_hora.strftime("%H:%M"),
        "sede": consultorio["ubicacion"],
        "consultorio": consultorio["nombre"],
        "llegada": llegada.strftime("%H:%M"),
        "cancelar_hasta": f"{limite_cancelar.day} de {MESES_LARGOS[limite_cancelar.month - 1].lower()} a las {limite_cancelar.strftime('%H:%M')} h",
    }

    return render_template("paciente/reservado.html", paciente=paciente, turno=datos_turno)


def traer_paciente():
    """Pide al backend los datos del paciente logueado (o de Marta, mientras no haya login)."""
    dni = session.get("dni", "99999999")
    paciente = requests.get(f"{API_URL}/pacientes/{dni}", timeout=5).json()["paciente"]
    paciente["iniciales"] = paciente["nombre"][0] + paciente["apellido"][0]
    return paciente


def armar_turno(turno):
    """Recibe un turno como lo manda la API y le agrega todos los textos que usan
    las páginas de Mis turnos, detalle y cancelar (médico, consultorio, fechas, plazos)."""
    medico = requests.get(f"{API_URL}/medicos/{turno['id_medico']}", timeout=5).json()
    consultorio = requests.get(f"{API_URL}/consultorios/{turno['id_consultorio']}", timeout=5).json()["consultorio"]

    especialidades = []
    especialidades_ids = []
    for item in medico.get("especialidades", []):
        especialidades.append(item["nombre"])
        especialidades_ids.append(item["id"])

    ahora = datetime.now()
    fecha_hora = leer_fecha(turno["fecha_hora"])
    limite_cancelar = fecha_hora - timedelta(hours=24)
    nombre_dia = DIAS[fecha_hora.weekday()]
    nombre_mes = MESES_LARGOS[fecha_hora.month - 1].lower()

    checkin_hora = None
    if turno.get("hora_checkin"):
        checkin_hora = leer_fecha(turno["hora_checkin"]).strftime("%H:%M")

    return {
        "id": turno["id"],
        "estado": turno["estado"],
        "codigo": f"Turno N.º {turno['id']}",
        "token": turno.get("string_token"),   # código de ingreso que usa recepción en el check-in
        "especialidad": ", ".join(especialidades),
        "especialidades_ids": especialidades_ids,
        "medico": medico["nombre"] + " " + medico["apellido"],
        "sede": consultorio["ubicacion"],
        "consultorio_nombre": consultorio["nombre"],
        "consultorio": consultorio["nombre"] + " · " + consultorio["ubicacion"],
        "duracion": DURACION_TURNO,
        # Distintas formas de mostrar la fecha, según la pantalla
        "dia": fecha_hora.day,
        "mes": MESES[fecha_hora.month - 1],
        "hora": fecha_hora.strftime("%H:%M"),
        "fecha": f"{nombre_dia} {fecha_hora.strftime('%d/%m/%Y')}",
        "fecha_corta": fecha_hora.strftime("%d/%m"),
        "fecha_numerica": fecha_hora.strftime("%d/%m/%Y"),
        "fecha_completa": f"{nombre_dia} {fecha_hora.day} de {nombre_mes} de {fecha_hora.year}",
        # Check-in: desde 15 minutos antes hasta 15 minutos después
        "checkin_desde": (fecha_hora - timedelta(minutes=15)).strftime("%H:%M"),
        "checkin_hasta": (fecha_hora + timedelta(minutes=15)).strftime("%H:%M"),
        "limite_ausente": (fecha_hora + timedelta(minutes=15)).strftime("%H:%M"),
        "checkin_hora": checkin_hora,
        # Plazos
        "es_proximo": fecha_hora >= ahora,
        "puede_cancelar": turno["estado"] == "reservado" and ahora <= limite_cancelar,
        "cancelar_hasta": limite_cancelar.strftime("%d/%m a las %H:%M h"),
        "emitido": None,
        "cancelado_el": None,
        "qr_url": None,
    }


@paciente_bp.route("/turnos")
def mis_turnos():
    """Mis turnos: los próximos y los anteriores del paciente, con filtros por estado y especialidad."""
    filtro_estado = request.args.get("estado", "")
    filtro_especialidad = request.args.get("especialidad", "")
    id_usuario = session.get("id_usuario", 1)

    try:
        paciente = traer_paciente()
        todos = requests.get(f"{API_URL}/turnos", timeout=5).json()

        # Solo los turnos de este paciente
        turnos = []
        for turno in todos:
            if turno["id_usuario"] == id_usuario:
                turnos.append(armar_turno(turno))

        respuesta = requests.get(f"{API_URL}/especialidades", timeout=5)
        especialidades = []
        if respuesta.status_code == 200:
            especialidades = respuesta.json()["especialidades"]

    except requests.exceptions.RequestException:
        return render_template("paciente/mis_turnos.html", paciente=None, total=0, proximos=[], anteriores=[],
                               estados=[], especialidades=[], filtro_estado=filtro_estado,
                               filtro_especialidad=filtro_especialidad,
                               error="No se pudo conectar con el servidor.")

    # Separamos en próximos y anteriores, aplicando los filtros elegidos
    proximos = []
    anteriores = []
    for turno in turnos:
        if filtro_estado != "" and turno["estado"] != filtro_estado:
            continue
        if filtro_especialidad != "" and int(filtro_especialidad) not in turno["especialidades_ids"]:
            continue
        if turno["es_proximo"]:
            proximos.append(turno)
        else:
            anteriores.append(turno)

    return render_template(
        "paciente/mis_turnos.html",
        paciente=paciente,
        total=len(turnos),
        proximos=proximos,
        anteriores=anteriores,
        estados=["reservado", "confirmado", "atendido", "cancelado", "ausente"],
        especialidades=especialidades,
        filtro_estado=filtro_estado,
        filtro_especialidad=filtro_especialidad,
        error=None,
    )


@paciente_bp.route("/turnos/<int:turno_id>")
def detalle_turno(turno_id):
    """Detalle de un turno del paciente, con su comprobante."""
    id_usuario = session.get("id_usuario", 1)
    hoy = date.today().strftime("%d/%m/%Y")

    try:
        paciente = traer_paciente()
        respuesta = requests.get(f"{API_URL}/turnos/{turno_id}", timeout=5)
        if respuesta.status_code != 200:
            return redirect(url_for("paciente.mis_turnos"))
        turno = respuesta.json()

        # Solo se muestra si el turno es de este paciente
        if turno["id_usuario"] != id_usuario:
            return redirect(url_for("paciente.mis_turnos"))

        datos_turno = armar_turno(turno)

    except requests.exceptions.RequestException:
        return redirect(url_for("paciente.mis_turnos"))

    return render_template("paciente/detalle_turno.html", paciente=paciente, turno=datos_turno,
                           hoy=hoy, mensaje=None, error=None)


@paciente_bp.route("/turnos/<int:turno_id>/cancelar", methods=["GET", "POST"])
def cancelar_turno(turno_id):
    """GET: pregunta si quiere cancelar. POST: le pide al backend que cancele el turno."""
    id_usuario = session.get("id_usuario", 1)
    ahora = datetime.now()
    vista = "confirmar"

    try:
        paciente = traer_paciente()

        if request.method == "POST":
            respuesta = requests.patch(f"{API_URL}/turnos/{turno_id}/cancelar", timeout=5)
            if respuesta.status_code == 200:
                vista = "exito"
            else:
                vista = "error"

        respuesta = requests.get(f"{API_URL}/turnos/{turno_id}", timeout=5)
        if respuesta.status_code != 200:
            return redirect(url_for("paciente.mis_turnos"))
        turno = respuesta.json()

        if turno["id_usuario"] != id_usuario:
            return redirect(url_for("paciente.mis_turnos"))

        datos_turno = armar_turno(turno)

    except requests.exceptions.RequestException:
        return redirect(url_for("paciente.mis_turnos"))

    return render_template(
        "paciente/cancelar_turno.html",
        paciente=paciente,
        turno=datos_turno,
        vista=vista,
        hoy=ahora.strftime("%d/%m/%Y"),
        cancelado_en=ahora.strftime("%d/%m/%Y a las %H:%M h"),
    )


@paciente_bp.route("/turnos/<int:turno_id>/comprobante")
def descargar_comprobante(turno_id):
    """Muestra el comprobante del turno (desde ahí se puede imprimir o guardar como PDF)."""
    return redirect(url_for("paciente.turno_reservado", turno_id=turno_id))

