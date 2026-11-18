"""Consultas SQL parametrizadas para la entidad de pacientes en `usuarios`."""

from typing import Any

from app.constants import ROL_PACIENTE
from app.db import get_connection


def obtener_por_dni(dni: str) -> dict[str, Any] | None:
    """Obtiene un paciente por su DNI."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, dni, nombre, apellido, email, activo
            FROM usuarios
            WHERE dni = %s AND rol = %s
            LIMIT 1
            """,
            (dni, ROL_PACIENTE),
        )
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def obtener_por_email(email: str) -> dict[str, Any] | None:
    """Obtiene un usuario por su email (para verificar unicidad)."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, dni, nombre, apellido, email, rol, activo
            FROM usuarios
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def listar() -> list[dict[str, Any]]:
    """Lista todos los usuarios con rol `paciente` ordenados por apellido y nombre."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, dni, nombre, apellido, email, activo
            FROM usuarios
            WHERE rol = %s
            ORDER BY apellido, nombre
            """,
            (ROL_PACIENTE,),
        )
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def actualizar(dni: str, datos: dict[str, str]) -> bool:
    """Actualiza `nombre`, `apellido` y/o `email` de un paciente por su DNI."""
    columnas_permitidas = ("nombre", "apellido", "email")
    asignaciones: list[str] = []
    valores: list[Any] = []

    for col in columnas_permitidas:
        if col in datos:
            asignaciones.append(f"{col} = %s")
            valores.append(datos[col])

    if not asignaciones:
        return False

    valores.extend([dni, ROL_PACIENTE])
    sql = f"UPDATE usuarios SET {', '.join(asignaciones)} WHERE dni = %s AND rol = %s"

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql, tuple(valores))
        connection.commit()
        return cursor.rowcount > 0
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def dar_baja(dni: str) -> bool:
    """Realiza la baja lógica (`activo = 0`) de un paciente por su DNI."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE usuarios SET activo = %s WHERE dni = %s AND rol = %s",
            (0, dni, ROL_PACIENTE),
        )
        connection.commit()
        return cursor.rowcount > 0
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
