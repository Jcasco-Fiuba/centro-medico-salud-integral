"""Validadores de entrada para registro, inicio de sesión y gestión de pacientes."""

import re
from typing import Any

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
DNI_REGEX = re.compile(r"^\d{7,8}$")

CAMPOS_PERMITIDOS_REGISTRO = frozenset(
    {"dni", "nombre", "apellido", "email", "password", "acepta_terminos"}
)
CAMPOS_PERMITIDOS_LOGIN = frozenset({"email", "password", "recordarme"})
CAMPOS_PERMITIDOS_ACTUALIZACION_PACIENTE = frozenset({"nombre", "apellido", "email"})

# Alineados con `backend/db/db.sql` (`VARCHAR(100)` para nombre y apellido,
# `VARCHAR(254)` para email y `VARCHAR(255)` para `password_hash` en `feature/db`).
MAX_NOMBRE_LEN = 100
MAX_APELLIDO_LEN = 100
MAX_EMAIL_LEN = 254
MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 128


def validar_dni(dni: Any) -> str:
    """Valida que el DNI sea una cadena de 7 u 8 dígitos ASCII."""
    if not isinstance(dni, str) or not dni.strip():
        raise ValueError("El DNI es obligatorio.")
    limpio = dni.strip()
    if not DNI_REGEX.match(limpio):
        raise ValueError("El DNI debe contener únicamente 7 u 8 dígitos numéricos.")
    return limpio


def validar_email_formato(email_raw: Any) -> str:
    """Valida formato y longitud máxima (254 caracteres según `usuarios.email`)."""
    if not isinstance(email_raw, str) or not email_raw.strip():
        raise ValueError("El campo 'email' es obligatorio.")
    email = email_raw.strip().lower()
    if len(email) > MAX_EMAIL_LEN:
        raise ValueError(f"El correo electrónico no puede superar {MAX_EMAIL_LEN} caracteres.")
    if ".." in email or not EMAIL_REGEX.match(email):
        raise ValueError("El correo electrónico no tiene un formato válido.")
    return email


def validar_payload_registro_paciente(
    data: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    """Valida el cuerpo JSON para ``POST /api/pacientes``.

    Acepta únicamente los datos personales y credenciales definidos para el
    registro público de pacientes (``dni``, ``nombre``, ``apellido``, ``email``,
    ``password``, ``acepta_terminos``). Rechaza campos adicionales como ``rol`` o ``activo``.
    """
    if not isinstance(data, dict):
        return None, "El cuerpo de la solicitud debe ser un objeto JSON válido."

    campos_extra = set(data.keys()) - CAMPOS_PERMITIDOS_REGISTRO
    if campos_extra:
        if "rol" in campos_extra or "activo" in campos_extra:
            return None, "No se permite especificar rol ni estado de cuenta en el registro público."
        return None, "La solicitud contiene campos no permitidos."

    nombre_raw = data.get("nombre")
    apellido_raw = data.get("apellido")
    dni_raw = data.get("dni")
    email_raw = data.get("email")
    password_raw = data.get("password")

    if not isinstance(nombre_raw, str) or not nombre_raw.strip():
        return None, "El campo 'nombre' es obligatorio."
    nombre = nombre_raw.strip()
    if len(nombre) > MAX_NOMBRE_LEN:
        return None, f"El campo 'nombre' no puede superar {MAX_NOMBRE_LEN} caracteres."

    if not isinstance(apellido_raw, str) or not apellido_raw.strip():
        return None, "El campo 'apellido' es obligatorio."
    apellido = apellido_raw.strip()
    if len(apellido) > MAX_APELLIDO_LEN:
        return None, f"El campo 'apellido' no puede superar {MAX_APELLIDO_LEN} caracteres."

    try:
        dni = validar_dni(dni_raw)
    except ValueError as exc:
        return None, str(exc)

    try:
        email = validar_email_formato(email_raw)
    except ValueError as exc:
        return None, str(exc)

    if not isinstance(password_raw, str) or not password_raw:
        return None, "El campo 'password' es obligatorio."
    if len(password_raw) < MIN_PASSWORD_LEN:
        return None, f"La contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres."
    if len(password_raw) > MAX_PASSWORD_LEN:
        return None, f"La contraseña no puede superar {MAX_PASSWORD_LEN} caracteres."

    acepta_terminos = data.get("acepta_terminos")
    if acepta_terminos is not True:
        return None, "Debés aceptar los términos y condiciones y la política de privacidad."

    return {
        "dni": dni,
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
        "password": password_raw,
        "acepta_terminos": True,
    }, None


def validar_payload_login(
    data: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    """Valida el cuerpo JSON para ``POST /api/auth/login``."""
    if not isinstance(data, dict):
        return None, "El cuerpo de la solicitud debe ser un objeto JSON válido."

    campos_extra = set(data.keys()) - CAMPOS_PERMITIDOS_LOGIN
    if campos_extra:
        return None, "La solicitud contiene campos no permitidos."

    try:
        email = validar_email_formato(data.get("email"))
    except ValueError as exc:
        return None, str(exc)

    password_raw = data.get("password")
    if not isinstance(password_raw, str) or not password_raw:
        return None, "El campo 'password' es obligatorio."
    if len(password_raw) > MAX_PASSWORD_LEN:
        return None, "Credenciales inválidas."

    recordarme_raw = data.get("recordarme", False)
    if not isinstance(recordarme_raw, bool):
        return None, "El campo 'recordarme' debe ser booleano."

    return {
        "email": email,
        "password": password_raw,
        "recordarme": recordarme_raw,
    }, None


def validar_payload_actualizacion_paciente(
    data: Any,
) -> tuple[dict[str, str] | None, str | None]:
    """Valida el cuerpo JSON para ``PATCH /api/pacientes/<dni>``."""
    if not isinstance(data, dict):
        return None, "El cuerpo de la solicitud debe ser un objeto JSON válido."

    if not data:
        return None, "No se enviaron datos para actualizar."

    campos_extra = set(data.keys()) - CAMPOS_PERMITIDOS_ACTUALIZACION_PACIENTE
    if campos_extra:
        return None, "La solicitud contiene campos que no se pueden modificar."

    limpios: dict[str, str] = {}

    if "nombre" in data:
        nombre_raw = data.get("nombre")
        if not isinstance(nombre_raw, str) or not nombre_raw.strip():
            return None, "El campo 'nombre' no puede estar vacío."
        nombre = nombre_raw.strip()
        if len(nombre) > MAX_NOMBRE_LEN:
            return None, f"El campo 'nombre' no puede superar {MAX_NOMBRE_LEN} caracteres."
        limpios["nombre"] = nombre

    if "apellido" in data:
        apellido_raw = data.get("apellido")
        if not isinstance(apellido_raw, str) or not apellido_raw.strip():
            return None, "El campo 'apellido' no puede estar vacío."
        apellido = apellido_raw.strip()
        if len(apellido) > MAX_APELLIDO_LEN:
            return None, f"El campo 'apellido' no puede superar {MAX_APELLIDO_LEN} caracteres."
        limpios["apellido"] = apellido

    if "email" in data:
        try:
            limpios["email"] = validar_email_formato(data.get("email"))
        except ValueError as exc:
            return None, str(exc)

    return limpios, None
