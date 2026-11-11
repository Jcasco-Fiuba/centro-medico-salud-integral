"""Emisión y verificación de JSON Web Tokens (JWT) con PyJWT."""

from datetime import datetime, timedelta, timezone
import os
from typing import Any

import jwt

from app.constants import (
    JWT_ALGORITHM,
    JWT_EXPIRATION_SECONDS,
    JWT_MIN_SECRET_LENGTH,
)

CLAIMS_OBLIGATORIOS = ("sub", "id_usuario", "dni", "iat", "exp")


class JWTConfigError(RuntimeError):
    """Error de configuración cuando falta o es débil la clave secreta de JWT."""


class TokenInvalidoError(ValueError):
    """Error cuando el token está ausente, vencido o no supera la validación."""


def _obtener_clave_jwt() -> str:
    """Obtiene y valida la clave secreta exclusiva desde el entorno."""
    secret_key = os.getenv("JWT_SECRET_KEY", "").strip()
    if len(secret_key) < JWT_MIN_SECRET_LENGTH:
        raise JWTConfigError(
            "La variable de entorno JWT_SECRET_KEY no está configurada o "
            f"tiene menos de {JWT_MIN_SECRET_LENGTH} caracteres."
        )
    return secret_key


def generar_access_token(id_usuario: int, dni: str) -> tuple[str, int]:
    """Genera un JWT firmado con HS256 para el usuario autenticado.

    El payload contiene exclusivamente los claims requeridos:
    - ``sub``: ``id_usuario`` como string (estándar RFC 7519).
    - ``id_usuario``: identificador numérico explícito.
    - ``dni``: DNI del usuario autenticado.
    - ``iat`` y ``exp``: marcas de emisión y expiración en UTC.

    No se incluyen otros datos personales porque un JWT firmado (JWS) está
    codificado en Base64URL pero no cifrado.
    """
    if isinstance(id_usuario, bool) or not isinstance(id_usuario, int) or id_usuario <= 0:
        raise ValueError("id_usuario debe ser un entero positivo.")
    if not isinstance(dni, str) or not dni.strip():
        raise ValueError("dni debe ser una cadena no vacía.")

    secret_key = _obtener_clave_jwt()
    ahora = datetime.now(timezone.utc)
    expiracion = ahora + timedelta(seconds=JWT_EXPIRATION_SECONDS)

    payload: dict[str, Any] = {
        "sub": str(id_usuario),
        "id_usuario": id_usuario,
        "dni": dni.strip(),
        "iat": int(ahora.timestamp()),
        "exp": int(expiracion.timestamp()),
    }

    token = jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)
    return token, JWT_EXPIRATION_SECONDS


def decodificar_y_validar_token(token: str) -> dict[str, Any]:
    """Decodifica y verifica firma, algoritmo fijo, expiración y claims obligatorios.

    Solo permite el algoritmo fijo ``HS256`` definido en el servidor, ignorando
    cualquier otro algoritmo declarado en el encabezado del token.
    """
    if not isinstance(token, str) or not token.strip():
        raise TokenInvalidoError("Token de autenticación vacío o ausente.")

    secret_key = _obtener_clave_jwt()

    try:
        payload = jwt.decode(
            token.strip(),
            secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"require": list(CLAIMS_OBLIGATORIOS)},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenInvalidoError("El token de autenticación ha expirado.") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidoError("El token de autenticación es inválido.") from exc

    sub = payload.get("sub")
    id_usuario = payload.get("id_usuario")
    dni = payload.get("dni")

    if not isinstance(sub, str) or not sub.strip():
        raise TokenInvalidoError("Claim 'sub' inválido en el token.")
    if isinstance(id_usuario, bool) or not isinstance(id_usuario, int) or id_usuario <= 0:
        raise TokenInvalidoError("Claim 'id_usuario' inválido en el token.")
    if sub != str(id_usuario):
        raise TokenInvalidoError("Inconsistencia entre 'sub' e 'id_usuario' en el token.")
    if not isinstance(dni, str) or not dni.strip():
        raise TokenInvalidoError("Claim 'dni' inválido en el token.")

    return {
        "sub": sub,
        "id_usuario": id_usuario,
        "dni": dni.strip(),
        "iat": payload["iat"],
        "exp": payload["exp"],
    }


def extraer_bearer_token(auth_header: str | None) -> str:
    """Extrae el token desde el encabezado ``Authorization: Bearer <token>``."""
    if not auth_header or not isinstance(auth_header, str):
        raise TokenInvalidoError("Falta el encabezado Authorization.")

    partes = auth_header.strip().split(" ")
    if len(partes) != 2 or partes[0].lower() != "bearer" or not partes[1].strip():
        raise TokenInvalidoError("El encabezado Authorization debe tener el formato 'Bearer <token>'.")

    return partes[1].strip()
