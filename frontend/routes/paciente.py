"""Rutas del portal autenticado de paciente"""
from datetime import datetime, timedelta

import requests
from flask import Blueprint, render_templates, session


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
        paciente = respuesta.json()
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
            consultorio = requests.get(f"{API_URL}/consultorios/{turno_elegido['id_consultorio']}", timeout=5).json()
 
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
 
    return render_template("paciente/portal.html", hoy=hoy, paciente=paciente,
                           proximo_turno=proximo_turno, error=None)
