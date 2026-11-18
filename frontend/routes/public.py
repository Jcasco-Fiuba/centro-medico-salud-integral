"""Rutas públicas: información del centro y consulta de disponibilidad."""

from flask import Blueprint, render_template


public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def inicio():
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
