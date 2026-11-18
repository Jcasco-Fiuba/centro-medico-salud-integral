"""Rutas públicas: información del centro y consulta de disponibilidad."""
from datetime import datetime
from flask import Blueprint, render_template, request
from services import api_client


public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def inicio():
    """Muestra el portal público: novedades, campañas de salud, ubicación y horarios."""
    novedades = [
        {
            "fecha": "Noviembre 2026",
            "titulo": "Nuevos turnos de Cardiología",
            "texto": "Sumamos horarios por la tarde para controles cardiológicos de lunes a viernes.",
        },
        {
            "fecha": "Octubre 2026",
            "titulo": "Check-in con código QR",
            "texto": "Al llegar, mostrá el código de tu turno en recepción y registrá tu llegada en segundos.",
        },
        {
            "fecha": "Septiembre 2026",
            "titulo": "Reservá desde tu casa",
            "texto": "Elegí especialidad, profesional, día y horario desde la web, sin llamar por teléfono.",
        },
    ]

    campanias = [
        {
            "titulo": "Control de presión arterial",
            "texto": "Durante noviembre, medición de presión sin turno previo en recepción.",
            "detalle": "Lunes a viernes · 8 a 12 h",
        },
        {
            "titulo": "Vacunación antigripal",
            "texto": "Campaña para mayores de 65 años y grupos de riesgo. Traé tu DNI.",
            "detalle": "Hasta el 30 de noviembre",
        },
        {
            "titulo": "Chequeo pediátrico escolar",
            "texto": "Apto físico y control de crecimiento para el inicio de clases.",
            "detalle": "Con turno en Pediatría",
        },
    ]

    horarios = [
        {"dias": "Lunes a viernes", "horas": "8 a 20 h"},
        {"dias": "Sábados", "horas": "8 a 13 h"},
        {"dias": "Domingos y feriados", "horas": "Cerrado"},
    ]

    return render_template(
        "public/inicio.html",
        novedades=novedades,
        campanias=campanias,
        horarios=horarios,
    )

@public_bp.get("/turnos-disponibles")
def turnos_disponibles():
    """Consulta pública de turnos libres: especialidad -> profesional -> día, sin iniciar sesión."""
    especialidad_id = request.args.get("especialidad", type=int)
    medico_id = request.args.get("medico", type=int)
    fecha = request.args.get("fecha", "")
    ahora = datetime.now()
    error = None

    #1 Especialidades para el primer desplegable
    respuesta, status = api_client.get("/api/especialidades")
    especialidades = []
    if status == 200:
        especialidades = respuesta["especialidades"]
    else:
        error = "No pudimos cargar las especialidades."

    #2 Medicos de la especialidad elegida
    medicos = []
    if especialidad_id:
        respuesta, status = api_client.get(f"/api/medicos?especialidad={especialidad_id}")
        if status == 200:
            medicos = respuesta

    #3 Horarios libres del médico en el día elegido
    horarios = []
    if medico_id and fecha:
        respuesta, status = api_client.get(f"/api/turnos/disponibles?medico={medico_id}&fecha={fecha}")
        if status == 200:
            for turno in respuesta:
                fecha_hora = datetime.strptime(turno["fecha_hora"], "%a, %d %b %Y %H:%M:%S GMT")
                if fecha_hora >= ahora:
                    horarios.append({"id": turno["id"], "hora": fecha_hora.strftime("%H:%M")})
        else:
            error = respuesta.get("error", "No pudimos cargar los horarios.")

    return render_template(
        "public/turnos_disponibles.html",
        especialidades=especialidades,
        medicos=medicos,
        horarios=horarios,
        especialidad_id=especialidad_id,
        medico_id=medico_id,
        fecha=fecha,
        hoy=ahora.strftime("%Y-%m-%d"),
        error=error,
    )
