"""Servicio de envío del QR de una reserva."""

import logging

from app import mailer
from app.repository import turnos as repo_turnos

logger = logging.getLogger(__name__)


def enviar_qr_reserva(turno_id: int, codigo: str, qr_png: bytes) -> str:
    """Devuelve 'enviado', 'no_configurado' o 'error'. Nunca anula la reserva."""
    if not mailer.mail_configurado():
        logger.warning("Correo deshabilitado o sin configurar; turno %s sin email", turno_id)
        return "no_configurado"

    try:
        reserva = repo_turnos.buscar_datos_correo_reserva(turno_id)
        if not reserva or reserva.get("estado") != "reservado" or not reserva.get("email"):
            raise ValueError("Reserva sin destinatario válido")
        mailer.enviar_email_qr_reserva(reserva, codigo, qr_png)
        return "enviado"
    except Exception as error:
        # Solo el tipo del error: no se loguea contraseña, token ni destinatario.
        logger.error("Falló el correo del turno %s: %s", turno_id, type(error).__name__)
        return "error"
