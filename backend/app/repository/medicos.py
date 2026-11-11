"""Consultas SQL parametrizadas para la entidad de médicos."""

from app.db import ejecutar_consulta, ejecutar_mutacion, get_connection

CAMPOS_EDITABLES_MEDICO = {"nombre", "apellido", "matricula", "id_consultorio"}


def listar_medicos() -> list[dict]:
    """Lista todos los médicos de la base de datos."""
    sql = """
    SELECT id, nombre, apellido, matricula, id_consultorio, activo
    FROM medicos
    ORDER BY apellido, nombre
    """
    return ejecutar_consulta(sql)


def listar_medicos_por_especialidad(id_especialidad: int) -> list[dict]:
    """Lista médicos activos asociados a la especialidad indicada."""
    sql = """
    SELECT DISTINCT m.id, m.nombre, m.apellido, m.matricula, m.id_consultorio, m.activo
    FROM medicos AS m
    INNER JOIN medicos_especialidades AS me ON me.id_medico = m.id
    WHERE me.id_especialidad = %(id_especialidad)s AND m.activo = TRUE
    ORDER BY m.apellido, m.nombre
    """
    return ejecutar_consulta(sql, {"id_especialidad": int(id_especialidad)})


def obtener_medico_por_id(id_medico) -> dict | None:
    """Devuelve el médico con el ID indicado o `None` si no existe."""
    sql = """
    SELECT id, nombre, apellido, matricula, id_consultorio, activo
    FROM medicos
    WHERE id = %(id)s
    """
    filas = ejecutar_consulta(sql, {"id": id_medico})
    return filas[0] if filas else None


def crear_medico(datos: dict) -> int:
    """Crea el médico y sus asociaciones de especialidad en una única transacción."""
    conexion = get_connection()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO medicos (nombre, apellido, matricula, id_consultorio)
            VALUES (%(nombre)s, %(apellido)s, %(matricula)s, %(id_consultorio)s)
            """,
            {
                "nombre": datos["nombre"],
                "apellido": datos["apellido"],
                "matricula": datos["matricula"],
                "id_consultorio": datos["id_consultorio"],
            },
        )
        id_medico = int(cursor.lastrowid)
        for id_especialidad in datos.get("especialidades", []):
            cursor.execute(
                """
                INSERT INTO medicos_especialidades (id_medico, id_especialidad)
                VALUES (%(id_medico)s, %(id_especialidad)s)
                """,
                {"id_medico": id_medico, "id_especialidad": id_especialidad},
            )
        conexion.commit()
        return id_medico
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def actualizar_medico(id_medico, campos: dict) -> dict | None:
    """Actualiza los campos recibidos del médico y retorna el médico actualizado."""
    campos_validos = {
        campo: valor
        for campo, valor in campos.items()
        if campo in CAMPOS_EDITABLES_MEDICO
    }
    if not campos_validos:
        return obtener_medico_por_id(id_medico)

    set_clause = ", ".join(f"{campo} = %({campo})s" for campo in campos_validos)
    sql = f"UPDATE medicos SET {set_clause} WHERE id = %(id)s"
    parametros = {**campos_validos, "id": id_medico}

    ejecutar_mutacion(sql, parametros)
    return obtener_medico_por_id(id_medico)


def dar_baja_medico(id_medico) -> dict | None:
    """Da de baja lógica al médico con el ID indicado y lo retorna actualizado."""
    sql = "UPDATE medicos SET activo = FALSE WHERE id = %(id)s"
    ejecutar_mutacion(sql, {"id": id_medico})
    return obtener_medico_por_id(id_medico)


def listar_especialidades_por_medico(id_medico) -> list[dict]:
    """Devuelve las especialidades asociadas a un médico."""
    sql = """
    SELECT especialidades.id, especialidades.nombre
    FROM especialidades
    INNER JOIN medicos_especialidades
        ON medicos_especialidades.id_especialidad = especialidades.id
    WHERE medicos_especialidades.id_medico = %(id_medico)s
    ORDER BY especialidades.nombre
    """
    return ejecutar_consulta(sql, {"id_medico": id_medico})


def borrar_especialidades_medico(id_medico) -> int:
    """Quita todas las especialidades asociadas a un médico."""
    sql = "DELETE FROM medicos_especialidades WHERE id_medico = %(id_medico)s"
    return ejecutar_mutacion(sql, {"id_medico": id_medico})


def asociar_medico_especialidad(datos: dict) -> int:
    """Asocia una especialidad a un médico."""
    sql = """
    INSERT INTO medicos_especialidades (id_medico, id_especialidad)
    VALUES (%(id_medico)s, %(id_especialidad)s)
    """
    return ejecutar_mutacion(
        sql,
        {
            "id_medico": datos["id_medico"],
            "id_especialidad": datos["id_especialidad"],
        },
    )
