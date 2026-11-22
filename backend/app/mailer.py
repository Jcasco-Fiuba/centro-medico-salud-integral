"""Construcción y envío de correos con Flask-Mail."""

import logging

from flask import current_app, render_template
from flask_mail import Mail, Message

from app import constants

logger = logging.getLogger(__name__)


def _mail() -> Mail:
    """Carga la configuración de correo en la app actual y devuelve el objeto Mail."""
    current_app.config.update(
        MAIL_SERVER=constants.MAIL_SERVER,
        MAIL_PORT=constants.MAIL_PORT,
        MAIL_USE_TLS=constants.MAIL_USE_TLS,
        MAIL_USE_SSL=constants.MAIL_USE_SSL,
        MAIL_USERNAME=constants.MAIL_USERNAME,
        MAIL_PASSWORD=constants.MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=constants.MAIL_DEFAULT_SENDER,
        MAIL_SUPPRESS_SEND=constants.MAIL_SUPPRESS_SEND,
    )
    return Mail(current_app)


def mail_configurado() -> bool:
    """Indica si hay credenciales y el envío no está suprimido (modo dev)."""
    return bool(constants.MAIL_USERNAME and constants.MAIL_PASSWORD) and not constants.MAIL_SUPPRESS_SEND


def enviar_email_qr_reserva(reserva: dict, codigo: str, qr_png: bytes) -> None:
    """Envía la confirmación con el QR como PNG inline. Propaga la excepción si falla el SMTP."""
    correo = _mail()  # registra Flask-Mail en la app antes de crear el Message

    mensaje = Message(
        subject="Confirmación de tu turno - Centro Médico Salud Integral",
        recipients=[reserva["email"]],
        html=render_template("emails/reserva_qr.html", reserva=reserva, codigo=codigo),
    )
    mensaje.body = (
        f"Tu turno N.º {reserva['id']} está reservado.\n"
        f"Fecha y hora: {reserva['fecha_hora']:%d/%m/%Y %H:%M}\n"
        "Presentá el QR de este correo en recepción.\n"
        f"Código alternativo: {codigo}\n"
    )
    mensaje.attach(
        "qr-turno.png",
        "image/png",
        qr_png,
        disposition="inline",
        headers={"Content-ID": "<qr_reserva>"},
    )
    correo.send(mensaje)
