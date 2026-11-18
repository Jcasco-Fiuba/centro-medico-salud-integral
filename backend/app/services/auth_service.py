"""Servicios de registro de pacientes, inicio de sesión, migración de hashes y autorización."""

from collections.abc import Callable
from functools import wraps
import hashlib
import hmac
import logging
import re
from typing import Any

from flask import g, jsonify, request
import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import check_password_hash, generate_password_hash

from app.constants import (
    JWT_EXPIRATION_SECONDS,
    JWT_REMEMBER_EXPIRATION_SECONDS,
    ROL_PACIENTE,
)
from app.db import get_connection
from app.repository import pacientes as pacientes_repository
from app.services.jwt_service import (
    JWTConfigError,
    TokenInvalidoError,
    decodificar_y_validar_token,
    extraer_bearer_token,
    generar_access_token,
)

logger = logging.getLogger(__name__)

# Formato canónico con Werkzeug que genera exactamente 98 caracteres
# (`pbkdf2:sha256:600000$<12-salt>$<64-hex>`), almacenado en la columna
# `usuarios.password_hash VARCHAR(255)` de `backend/db/db.sql`
# (y ampliada desde instalaciones previas por `001_expand_auth_fields.sql`).
PASSWORD_HASH_METHOD = "pbkdf2:sha256:600000"
PASSWORD_SALT_LENGTH = 12
_PREFIJO_CANONICO = f"{PASSWORD_HASH_METHOD}$"

# Formato PBKDF2 legado de `feature/pacientes`: `<32-hex-salt>$<64-hex-sha256>` (97 chars).
_LEGACY_PBKDF2_RE = re.compile(r"^([0-9a-f]{32})\$([0-9a-f]{64})$")
_LEGACY_PBKDF2_ITERATIONS = 100000

# Hash ficticio para homogeneizar tiempos de respuesta cuando el email no existe
# o cuando el hash almacenado no tiene un formato válido.
_DUMMY_PASSWORD_HASH = generate_password_hash(
    "dummy-password-for-timing-uniformity",
    method=PASSWORD_HASH_METHOD,
    salt_length=PASSWORD_SALT_LENGTH,
)

MENSAJE_CREDENCIALES_INVALIDAS = "Credenciales inválidas."


class AuthServiceError(Exception):
    """Error base para la capa de servicios de autenticación."""


class UsuarioDuplicadoError(AuthServiceError):
    """Se lanza cuando el DNI o el correo electrónico ya están registrados."""


class CredencialesInvalidasError(AuthServiceError):
    """Se lanza cuando las credenciales no son válidas o la cuenta está inactiva."""


class PermisoDenegadoError(AuthServiceError):
    """Se lanza cuando el usuario autenticado no tiene el rol requerido."""


class PacienteNoEncontradoError(AuthServiceError):
    """Se lanza cuando no existe el paciente consultado."""


class EstadoPacienteConflictoError(AuthServiceError):
    """Se lanza cuando el paciente ya se encuentra dado de baja."""


def generar_hash_canonico(password: str) -> str:
    """Genera un hash PBKDF2-SHA256 de 98 caracteres mediante `werkzeug.security`."""
    return generate_password_hash(
        password,
        method=PASSWORD_HASH_METHOD,
        salt_length=PASSWORD_SALT_LENGTH,
    )


def verificar_password_almacenada(
    password_hash_almacenado: str,
    password: str,
) -> tuple[bool, bool]:
    """Verifica una contraseña contra el hash almacenado y señala si requiere migración.

    Retorna `(es_valida, requiere_rehash)`:
    - Hashes de `werkzeug.security` (`pbkdf2:...` o `scrypt:...`): se validan con
      `check_password_hash`. Si usan un formato anterior al canónico, marca
      `requiere_rehash = True`.
    - Hashes PBKDF2 de `feature/pacientes` (`<32-hex-salt>$<64-hex-sha256>`): se
      validan en tiempo constante con `hmac.compare_digest` y marcan
      `requiere_rehash = True` para migrar la cuenta al formato canónico.
    - Contraseñas en texto plano o formatos desconocidos: se rechazan siempre
      (nunca se aceptan contraseñas en claro como fallback).
    """
    if not isinstance(password_hash_almacenado, str) or not password_hash_almacenado:
        check_password_hash(_DUMMY_PASSWORD_HASH, password)
        return False, False

    if password_hash_almacenado.startswith(("pbkdf2:", "scrypt:")):
        try:
            valida = check_password_hash(password_hash_almacenado, password)
        except ValueError:
            return False, False
        requiere_rehash = valida and (
            not password_hash_almacenado.startswith(_PREFIJO_CANONICO)
            or len(password_hash_almacenado) > 100
        )
        return valida, requiere_rehash

    match_legacy = _LEGACY_PBKDF2_RE.match(password_hash_almacenado)
    if match_legacy is not None:
        sal_hex, digest_esperado = match_legacy.groups()
        digest_calculado = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(sal_hex),
            _LEGACY_PBKDF2_ITERATIONS,
        ).hex()
        valida = hmac.compare_digest(digest_calculado, digest_esperado)
        return valida, valida

    # Cualquier otro formato (incluyendo texto plano en seeds sin hashear) se rechaza.
    check_password_hash(_DUMMY_PASSWORD_HASH, password)
    return False, False


def registrar_paciente(datos: dict[str, str]) -> dict[str, Any]:
    """Registra un nuevo usuario con rol ``paciente`` en la tabla ``usuarios``.

    El rol y el estado ``activo`` se asignan exclusivamente en el servidor.
    La contraseña se almacena con el hash canónico de `werkzeug.security` (98 chars).
    """
    password_hash = generar_hash_canonico(datos["password"])

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT dni, email
            FROM usuarios
            WHERE dni = %s OR email = %s
            LIMIT 1
            """,
            (datos["dni"], datos["email"]),
        )
        existente = cursor.fetchone()
        if existente is not None:
            connection.rollback()
            raise UsuarioDuplicadoError(
                "Ya existe un usuario registrado con ese DNI o correo electrónico."
            )

        cursor.execute(
            """
            INSERT INTO usuarios (dni, nombre, apellido, email, password_hash, rol, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                datos["dni"],
                datos["nombre"],
                datos["apellido"],
                datos["email"],
                password_hash,
                ROL_PACIENTE,
                1,
            ),
        )
        id_usuario = int(cursor.lastrowid)
        connection.commit()
    except UsuarioDuplicadoError:
        raise
    except mysql.connector.IntegrityError as exc:
        connection.rollback()
        if exc.errno == errorcode.ER_DUP_ENTRY:
            raise UsuarioDuplicadoError(
                "Ya existe un usuario registrado con ese DNI o correo electrónico."
            ) from exc
        logger.error("Error de integridad al registrar paciente: errno=%s", exc.errno)
        raise
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    return {
        "id": id_usuario,
        "id_usuario": id_usuario,
        "dni": datos["dni"],
        "nombre": datos["nombre"],
        "apellido": datos["apellido"],
        "email": datos["email"],
        "rol": ROL_PACIENTE,
        "activo": True,
    }


def _migrar_hash_usuario(id_usuario: int, nuevo_hash: str) -> None:
    """Actualiza el hash de contraseña de un usuario al formato canónico."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE usuarios SET password_hash = %s WHERE id = %s",
            (nuevo_hash, id_usuario),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        logger.warning("No se pudo actualizar el hash al formato canónico para id=%s", id_usuario)
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def autenticar_usuario(email: str, password: str, recordarme: bool = False) -> dict[str, Any]:
    """Autentica una cuenta activa por email y contraseña, y emite un JWT.

    Devuelve un error uniforme ante email inexistente, contraseña incorrecta,
    hash en texto plano o cuenta inactiva para no filtrar el estado de la cuenta.
    """
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, dni, nombre, apellido, email, password_hash, rol, activo
            FROM usuarios
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )
        usuario = cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    if usuario is None:
        check_password_hash(_DUMMY_PASSWORD_HASH, password)
        raise CredencialesInvalidasError(MENSAJE_CREDENCIALES_INVALIDAS)

    password_hash = usuario.get("password_hash") or ""
    password_valida, requiere_rehash = verificar_password_almacenada(password_hash, password)
    cuenta_activa = bool(usuario.get("activo"))

    if not password_valida or not cuenta_activa:
        raise CredencialesInvalidasError(MENSAJE_CREDENCIALES_INVALIDAS)

    id_usuario = int(usuario["id"])
    dni = str(usuario["dni"])

    if requiere_rehash:
        _migrar_hash_usuario(id_usuario, generar_hash_canonico(password))

    ttl = JWT_REMEMBER_EXPIRATION_SECONDS if recordarme else JWT_EXPIRATION_SECONDS
    access_token, expires_in = generar_access_token(
        id_usuario=id_usuario,
        dni=dni,
        expiracion_segundos=ttl,
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "usuario": {
            "id": id_usuario,
            "id_usuario": id_usuario,
            "dni": dni,
            "nombre": usuario["nombre"],
            "apellido": usuario["apellido"],
            "email": usuario["email"],
            "rol": usuario["rol"],
        },
    }


def obtener_perfil_paciente(dni: str) -> dict[str, Any]:
    """Obtiene los datos públicos de un paciente por su DNI."""
    paciente = pacientes_repository.obtener_por_dni(dni)
    if paciente is None:
        raise PacienteNoEncontradoError("Paciente no encontrado.")
    return {
        "dni": str(paciente["dni"]),
        "nombre": paciente["nombre"],
        "apellido": paciente["apellido"],
        "email": paciente["email"],
    }


def listar_pacientes_registrados() -> list[dict[str, Any]]:
    """Devuelve el listado de pacientes (uso exclusivo de administración)."""
    filas = pacientes_repository.listar()
    return [
        {
            "dni": str(fila["dni"]),
            "nombre": fila["nombre"],
            "apellido": fila["apellido"],
            "email": fila["email"],
            "activo": bool(fila["activo"]),
        }
        for fila in filas
    ]


def actualizar_perfil_paciente(dni: str, datos: dict[str, str]) -> None:
    """Actualiza nombre, apellido o email de un paciente existente."""
    paciente = pacientes_repository.obtener_por_dni(dni)
    if paciente is None:
        raise PacienteNoEncontradoError("Paciente no encontrado.")

    if "email" in datos:
        existente = pacientes_repository.obtener_por_email(datos["email"])
        if existente is not None and str(existente["dni"]) != str(dni):
            raise UsuarioDuplicadoError("El correo electrónico ya está registrado.")

    try:
        pacientes_repository.actualizar(dni, datos)
    except mysql.connector.IntegrityError as exc:
        if exc.errno == errorcode.ER_DUP_ENTRY:
            raise UsuarioDuplicadoError("El correo electrónico ya está registrado.") from exc
        raise


def dar_baja_logica_paciente(dni: str) -> None:
    """Marca como inactivo (`activo = 0`) a un paciente existente."""
    paciente = pacientes_repository.obtener_por_dni(dni)
    if paciente is None:
        raise PacienteNoEncontradoError("Paciente no encontrado.")
    if not bool(paciente.get("activo")):
        raise EstadoPacienteConflictoError("El paciente ya está dado de baja.")
    pacientes_repository.dar_baja(dni)


def obtener_usuario_autenticado_desde_header(auth_header: str | None) -> dict[str, Any]:
    """Valida el JWT del encabezado ``Authorization`` y verifica estado actual en MySQL.

    La identidad del usuario se deriva exclusivamente de los claims firmados
    (``id_usuario`` y ``dni``) y se contrasta contra la base de datos para
    confirmar que la cuenta sigue activa y obtener su rol vigente.
    """
    token = extraer_bearer_token(auth_header)
    claims = decodificar_y_validar_token(token)

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, dni, nombre, apellido, email, rol, activo
            FROM usuarios
            WHERE id = %s AND dni = %s
            LIMIT 1
            """,
            (claims["id_usuario"], claims["dni"]),
        )
        usuario = cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    if usuario is None or not bool(usuario.get("activo")):
        raise TokenInvalidoError("La cuenta asociada al token no se encuentra activa.")

    id_usuario = int(usuario["id"])
    return {
        "id": id_usuario,
        "id_usuario": id_usuario,
        "dni": str(usuario["dni"]),
        "nombre": usuario["nombre"],
        "apellido": usuario["apellido"],
        "email": usuario["email"],
        "rol": usuario["rol"],
        "activo": bool(usuario["activo"]),
    }


def requiere_autenticacion(
    roles: tuple[str, ...] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorador para proteger endpoints que requieren JWT válido y cuenta activa."""

    def decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view_func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            auth_header = request.headers.get("Authorization")
            try:
                usuario = obtener_usuario_autenticado_desde_header(auth_header)
            except TokenInvalidoError:
                return jsonify({"error": "No autenticado. Token ausente, inválido o expirado."}), 401
            except JWTConfigError:
                logger.error("Error de configuración JWT al validar solicitud.")
                return jsonify({"error": "Error de configuración del servidor."}), 500
            except mysql.connector.Error:
                logger.error("Error de base de datos al verificar el estado del usuario autenticado.")
                return jsonify({"error": "Error interno al verificar la sesión."}), 500

            if roles is not None and usuario["rol"] not in roles:
                return jsonify({"error": "No tiene permisos para realizar esta operación."}), 403

            g.usuario_actual = usuario
            g.usuario = usuario
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
