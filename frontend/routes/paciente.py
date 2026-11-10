"""Rutas del portal autenticado de paciente"""
from datetime import datetime, timedelta

import requests
from flask import Blueprint, redirect, render_template, request, session, url_for


paciente_bp = Blueprint("paciente", __name__, url_prefix="/paciente")

API_URL = "http://127.0.0.1:5000/api"
 
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
 
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
