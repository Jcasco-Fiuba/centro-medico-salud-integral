"""Consultas SQL parametrizadas para la entidad de turnos."""

from datetime import datetime, timedelta

from app.db import ejecutar_consulta, ejecutar_mutacion, get_connection


def listar_turnos(medico=None, estado=None):
    """Lista los turnos aplicando filtros opcionales por médico y/o estado."""
    if medico is not None and estado is not None:
        sql = """
        SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado, hora_checkin
        FROM turnos
        WHERE id_medico = %(medico)s AND estado = %(estado)s
        ORDER BY fecha_hora
        """
        parametros = {"medico": int(medico), "estado": estado}
    elif medico is not None:
        sql = """
        SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado, hora_checkin
        FROM turnos
        WHERE id_medico = %(medico)s
        ORDER BY fecha_hora
        """
        parametros = {"medico": int(medico)}
    elif estado is not None:
        sql = """
        SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado, hora_checkin
        FROM turnos
        WHERE estado = %(estado)s
        ORDER BY fecha_hora
        """
        parametros = {"estado": estado}
    else:
        sql = """
        SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado, hora_checkin
        FROM turnos
        ORDER BY fecha_hora
        """
        parametros = {}
    return ejecutar_consulta(sql, parametros)


def buscar_turno_id(id_turno):
    """Recibe un ID de turno y retorna su detalle."""
    sql = """
    SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado, string_token, hora_checkin
    FROM turnos
    WHERE id = %(id)s
    """
    filas = ejecutar_consulta(sql, {"id": int(id_turno)})
    return filas[0] if filas else None


def buscar_turno_dni(dni: str) -> list[dict]:
    """Recibe el DNI de un paciente y retorna el detalle de sus turnos."""
    sql = """
    SELECT turnos.id, turnos.id_usuario, turnos.id_medico, turnos.id_consultorio,
           turnos.fecha_hora, turnos.estado, turnos.hora_checkin,
           medicos.nombre AS medico_nombre, medicos.apellido AS medico_apellido,
           consultorios.nombre AS consultorio, consultorios.ubicacion
    FROM turnos
    INNER JOIN usuarios ON usuarios.id = turnos.id_usuario
    INNER JOIN medicos ON medicos.id = turnos.id_medico
    INNER JOIN consultorios ON consultorios.id = turnos.id_consultorio
    WHERE usuarios.dni = %(dni)s
    ORDER BY turnos.fecha_hora
    """
    return ejecutar_consulta(sql, {"dni": str(dni)})


def buscar_turnos_disponibles(medico_id: int, fecha: str) -> list[dict]:
    """Busca y devuelve los turnos disponibles de un médico en una fecha determinada."""
    sql = """
    SELECT id, id_medico, id_consultorio, fecha_hora, estado
    FROM turnos
    WHERE id_medico = %(medico_id)s AND estado = 'disponible' AND DATE(fecha_hora) = %(fecha)s
    ORDER BY fecha_hora
    """
    return ejecutar_consulta(sql, {"medico_id": int(medico_id), "fecha": fecha})


def buscar_turno_por_token(string_token: str) -> dict | None:
    """Busca un turno mediante el token del QR y devuelve sus datos con paciente y médico."""
    sql = """
    SELECT turnos.id, turnos.id_usuario, turnos.id_medico, turnos.id_consultorio,
           turnos.fecha_hora, turnos.estado, turnos.string_token, turnos.hora_checkin,
           usuarios.dni, usuarios.nombre AS paciente_nombre, usuarios.apellido AS paciente_apellido,
           medicos.nombre AS medico_nombre, medicos.apellido AS medico_apellido
    FROM turnos
    LEFT JOIN usuarios ON usuarios.id = turnos.id_usuario
    LEFT JOIN medicos ON medicos.id = turnos.id_medico
    WHERE turnos.string_token = %(string_token)s
    """
    filas = ejecutar_consulta(sql, {"string_token": string_token})
    return filas[0] if filas else None


def verificar_turnos_superpuestos(id_medico: int, id_consultorio: int, fecha_hora: datetime) -> bool:
    """Verifica si el médico o el consultorio tienen un turno activo superpuesto en la ventana de 30 minutos."""
    inicio_nuevo = fecha_hora
    fin_nuevo = inicio_nuevo + timedelta(minutes=30)

    sql = """
    SELECT id, fecha_hora
    FROM turnos
    WHERE estado != 'cancelado'
      AND (id_medico = %(id_medico)s OR id_consultorio = %(id_consultorio)s)
    """
    turnos_existentes = ejecutar_consulta(
        sql,
        {"id_medico": int(id_medico), "id_consultorio": int(id_consultorio)},
    )

    for turno in turnos_existentes:
        inicio_existente = turno["fecha_hora"]
        if isinstance(inicio_existente, str):
            inicio_existente = datetime.fromisoformat(inicio_existente)
        fin_existente = inicio_existente + timedelta(minutes=30)
        if inicio_nuevo < fin_existente and fin_nuevo > inicio_existente:
            return True

    return False


def crear_turno(datos: dict) -> dict | None:
    """Crea un turno disponible si no hay superposición de horario."""
    fecha_hora = datos["fecha_hora"]
    if isinstance(fecha_hora, str):
        fecha_hora = datetime.fromisoformat(fecha_hora)

    if verificar_turnos_superpuestos(datos["id_medico"], datos["id_consultorio"], fecha_hora):
        return None

    sql = """
    INSERT INTO turnos (id_medico, id_consultorio, fecha_hora)
    VALUES (%(id_medico)s, %(id_consultorio)s, %(fecha_hora)s)
    """
    id_turno = ejecutar_mutacion(
        sql,
        {
            "id_medico": int(datos["id_medico"]),
            "id_consultorio": int(datos["id_consultorio"]),
            "fecha_hora": fecha_hora,
        },
    )
    return buscar_turno_id(id_turno)


def actualizar_reserva_turno(turno_id: int, usuario_id: int, token: str) -> dict | None:
    """Asigna un turno disponible al paciente autenticado y guarda su token QR."""
    turno = buscar_turno_id(turno_id)
    if not turno or turno["estado"] != "disponible":
        return None

    sql = """
    UPDATE turnos
    SET id_usuario = %(usuario_id)s, string_token = %(token)s, estado = 'reservado'
    WHERE id = %(turno_id)s AND estado = 'disponible'
    """
    ejecutar_mutacion(
        sql,
        {
            "usuario_id": int(usuario_id),
            "token": token,
            "turno_id": int(turno_id),
        },
    )

    turno_actualizado = buscar_turno_id(turno_id)
    if not turno_actualizado or turno_actualizado.get("string_token") != token:
        return None
    return turno_actualizado


def actualizar_cancelacion_turno(id_turno: int, usuario_id: int | None = None, liberar: bool = True) -> dict | None:
    """Cancela un turno reservado y libera la franja en una transacción."""
    conexion = get_connection()
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado
            FROM turnos
            WHERE id = %(id)s
            FOR UPDATE
            """,
            {"id": int(id_turno)},
        )
        turno = cursor.fetchone()
        if not turno or turno.get("estado") != "reservado":
            conexion.rollback()
            return None
        if usuario_id is not None and turno.get("id_usuario") != int(usuario_id):
            conexion.rollback()
            return None

        where = "id = %(id)s AND estado = 'reservado'"
        parametros: dict[str, int] = {"id": int(id_turno)}
        if usuario_id is not None:
            where += " AND id_usuario = %(usuario_id)s"
            parametros["usuario_id"] = int(usuario_id)

        cursor.execute(
            f"UPDATE turnos SET estado = 'cancelado' WHERE {where}",
            parametros,
        )
        if cursor.rowcount != 1:
            conexion.rollback()
            return None

        if liberar:
            cursor.execute(
                """
                INSERT INTO turnos (id_medico, id_consultorio, fecha_hora)
                VALUES (%(id_medico)s, %(id_consultorio)s, %(fecha_hora)s)
                """,
                {
                    "id_medico": turno["id_medico"],
                    "id_consultorio": turno["id_consultorio"],
                    "fecha_hora": turno["fecha_hora"],
                },
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()

    return buscar_turno_id(id_turno)


def registrar_checkin(id_turno: int, hora_llegada: datetime) -> dict | None:
    """Pasa un turno de 'reservado' a 'confirmado' y registra `hora_checkin`."""
    turno = buscar_turno_id(id_turno)
    if not turno or turno["estado"] != "reservado":
        return None

    sql = """
    UPDATE turnos
    SET estado = 'confirmado', hora_checkin = %(hora_llegada)s
    WHERE id = %(id)s AND estado = 'reservado'
    """
    ejecutar_mutacion(sql, {"id": int(id_turno), "hora_llegada": hora_llegada})
    return buscar_turno_por_token(turno["string_token"]) if turno.get("string_token") else buscar_turno_id(id_turno)


def buscar_turnos_sala_espera(fecha) -> list[dict]:
    """Devuelve los turnos confirmados del día ordenados por `hora_checkin`."""
    sql = """
    SELECT turnos.id, turnos.fecha_hora, turnos.hora_checkin, turnos.estado,
           usuarios.dni, usuarios.nombre AS paciente_nombre, usuarios.apellido AS paciente_apellido,
           medicos.nombre AS medico_nombre, medicos.apellido AS medico_apellido
    FROM turnos
    INNER JOIN usuarios ON usuarios.id = turnos.id_usuario
    INNER JOIN medicos ON medicos.id = turnos.id_medico
    WHERE turnos.estado = 'confirmado'
      AND DATE(turnos.fecha_hora) = %(fecha)s
    ORDER BY turnos.hora_checkin
    """
    return ejecutar_consulta(sql, {"fecha": str(fecha)})


def actualizar_turno_atendido(id_turno: int) -> dict | None:
    """Cambia el estado de un turno de 'confirmado' a 'atendido'."""
    turno = buscar_turno_id(id_turno)
    if not turno or turno["estado"] != "confirmado":
        return None

    sql = """
    UPDATE turnos
    SET estado = 'atendido'
    WHERE id = %(id)s AND estado = 'confirmado'
    """
    ejecutar_mutacion(sql, {"id": int(id_turno)})
    return buscar_turno_id(id_turno)


def marcar_turno_ausente(id_turno: int) -> dict | None:
    """Cambia el estado de un turno de 'reservado' a 'ausente'."""
    turno = buscar_turno_id(id_turno)
    if not turno or turno["estado"] != "reservado":
        return None

    sql = """
    UPDATE turnos
    SET estado = 'ausente'
    WHERE id = %(id)s AND estado = 'reservado'
    """
    ejecutar_mutacion(sql, {"id": int(id_turno)})
    return buscar_turno_por_token(turno["string_token"]) if turno.get("string_token") else buscar_turno_id(id_turno)
