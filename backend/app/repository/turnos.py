from datetime import datetime, timedelta
from app.db import ejecutar_consulta, ejecutar_mutacion
# ---------------------------------------------------------------
# Queries de turnos
# ---------------------------------------------------------------

def listar_turnos(medico=None, estado=None):
    if medico is not None and estado is not None:
        sql = """
        SELECT *
        FROM turnos
        WHERE id_medico = %(medico)s AND estado = %(estado)s
        """
        parametros = {"medico": medico, "estado": estado}
    elif medico is not None:
        sql = """
        SELECT *
        FROM turnos
        WHERE id_medico = %(medico)s
        """
        parametros = {"medico": medico}
    elif estado is not None:
        sql = """
        SELECT *
        FROM turnos
        WHERE estado = %(estado)s
        """
        parametros = {"estado": estado}
    else:
        sql = """
        SELECT *
        FROM turnos
        """
        parametros = {}
    return ejecutar_consulta(sql, parametros)


def buscar_turno_id(id):
    """
    Recibe un id de turno y retorna el detalle del mismo.
    """

    sql = """
    SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado, string_token, hora_checkin
    FROM turnos
    WHERE id = %(id)s
    """
    filas = ejecutar_consulta(sql, {'id': id})

    return filas[0] if filas else None


def buscar_turno_dni(dni) -> list[dict]:
    """
    Recibe el dni de un paciente y retorna el detalle de sus turnos.
    """

    sql = """
    SELECT turnos.id, turnos.fecha_hora, turnos.estado, turnos.string_token,
           medicos.nombre AS medico_nombre, medicos.apellido AS medico_apellido,
           consultorios.nombre AS consultorio, consultorios.ubicacion
    FROM turnos
    INNER JOIN usuarios ON usuarios.id = turnos.id_usuario
    INNER JOIN medicos ON medicos.id = turnos.id_medico
    INNER JOIN consultorios ON consultorios.id = turnos.id_consultorio
    WHERE usuarios.dni = %(dni)s
    ORDER BY turnos.fecha_hora
    """

    return ejecutar_consulta(sql, {'dni': dni})


def buscar_turno_por_medico(medico, estado) -> list[dict]:
    """
    Recibe el id de un medico y un estado, y lista los turnos
    del medico con el estado seleccionados.
    """

    sql = """
    SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado
    FROM turnos
    WHERE id_medico = %(medico)s AND estado = %(estado)s
    """

    return ejecutar_consulta(sql, {'medico': medico, 'estado': estado})


def buscar_turnos_disponibles(medico_id, fecha) -> list[dict]:
    """
    Busca y devuelve los turnos disponibles de un médico en una fecha determinada.
    """

    sql = """
    SELECT id, id_medico, id_consultorio, fecha_hora
    FROM turnos
    WHERE id_medico = %(medico_id)s AND estado = 'disponible' AND DATE(fecha_hora) = %(fecha)s
    ORDER BY fecha_hora
    """

    return ejecutar_consulta(sql, {'medico_id': medico_id, 'fecha': fecha})


def buscar_turno_por_token(string_token) -> dict | None:
    """
    Busca un turno mediante el token y devuelve sus datos. Si no existe, devuelve None.
    """

    sql = """
    SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado, string_token, hora_checkin
    FROM turnos
    WHERE string_token = %(string_token)s
    """
    filas = ejecutar_consulta(sql, {'string_token': string_token})

    return filas[0] if filas else None


def verificar_turnos_superpuestos(id_medico, id_consultorio, fecha_hora):

    inicio_nuevo = fecha_hora
    fin_nuevo = inicio_nuevo + timedelta(minutes=30)

    sql = """
    SELECT id, fecha_hora
    FROM turnos
    WHERE estado != 'cancelado'
    AND (id_medico = %(id_medico)s OR id_consultorio = %(id_consultorio)s)
    """

    parametros = {
        "id_medico": id_medico,
        "id_consultorio": id_consultorio
    }

    turnos = ejecutar_consulta(sql, parametros)

    for turno in turnos:
        inicio_existente = turno["fecha_hora"]
        fin_existente = inicio_existente + timedelta(minutes=30)

        if inicio_nuevo < fin_existente and fin_nuevo > inicio_existente:
            return True

    return False


def crear_turno(datos: dict) -> dict | None:
    """
    Recibe datos del nuevo turno y lo agrega a la base de datos, si el medico ya
    tiene un turno en ese horario retorna None.
    """

    if verificar_turnos_superpuestos(
        datos['id_medico'],
        datos['id_consultorio'],
        datos['fecha_hora']
    ):
        return None

    sql = """
    INSERT INTO turnos (id_medico, id_consultorio, fecha_hora)
    VALUES (%(id_medico)s, %(id_consultorio)s, %(fecha_hora)s)
    """
    id_turno = ejecutar_mutacion(sql, {
        'id_medico': datos['id_medico'],
        'id_consultorio': datos['id_consultorio'],
        'fecha_hora': datos['fecha_hora']
    })

    return buscar_turno_id(id_turno)


def actualizar_reserva_turno(turno_id, usuario_id, token) -> dict | None:
    """
    Recibe el id de un turno, el id de un usuario y un token. Si el turno
    esta disponible, se lo asigna al usuario, guarda el token, lo pasa a
    reservado y devuelve el turno actualizado. Si no se pudo reservar,
    retorna None.
    """

    turno = buscar_turno_id(turno_id)

    if not turno or turno['estado'] != 'disponible':
        return None

    sql = """
    UPDATE turnos
    SET id_usuario = %(usuario_id)s, string_token = %(token)s, estado = 'reservado'
    WHERE id = %(turno_id)s AND estado = 'disponible'
    """
    ejecutar_mutacion(sql, {
        'usuario_id': usuario_id,
        'token': token,
        'turno_id': turno_id
    })

    turno = buscar_turno_id(turno_id)

    if turno['string_token'] != token:
        return None

    return turno


def actualizar_cancelacion_turno(id, usuario_id, liberar=True) -> dict | None:
    """
    Cancela un turno reservado que pertenece al paciente indicado y
    devuelve el resultado. Permitir liberar el horario.
    """

    turno = buscar_turno_id(id)

    if not turno or turno['estado'] != 'reservado' or turno['id_usuario'] != usuario_id:
        return None

    sql = """
    UPDATE turnos
    SET estado = 'cancelado'
    WHERE id = %(id)s AND id_usuario = %(usuario_id)s AND estado = 'reservado'
    """
    ejecutar_mutacion(sql, {'id': id, 'usuario_id': usuario_id})

    turno = buscar_turno_id(id)

    if liberar:
        crear_turno({
            'id_medico': turno['id_medico'],
            'id_consultorio': turno['id_consultorio'],
            'fecha_hora': turno['fecha_hora']
        })

    return turno

# ---------------------------------------------------------------
# Queries de recepcion
# ---------------------------------------------------------------

def registrar_checkin(id, hora_llegada) -> dict | None:
    """
    Cambia el estado de un turno de "reservado" a "confirmado",
    registra la hora de llegada y devuelve el turno actualizado.
    """

    turno = buscar_turno_id(id)

    if not turno or turno['estado'] != 'reservado':
        return None

    sql = """
    UPDATE turnos
    SET estado = 'confirmado', hora_checkin = %(hora_llegada)s
    WHERE id = %(id)s AND estado = 'reservado'
    """
    ejecutar_mutacion(sql, {'id': id, 'hora_llegada': hora_llegada})

    turno = buscar_turno_id(id)

    return turno


def buscar_turnos_sala_espera(fecha) -> list[dict]:
    """
    Devuelve los turnos confirmados del dia ordenados por hora de llegada (check-in).
    """

    sql = """
    SELECT turnos.id, turnos.fecha_hora, turnos.hora_checkin,
    usuarios.dni, usuarios.nombre AS paciente_nombre, usuarios.apellido AS paciente_apellido,
    medicos.nombre AS medico_nombre, medicos.apellido AS medico_apellido
    FROM turnos
    INNER JOIN usuarios ON usuarios.id = turnos.id_usuario
    INNER JOIN medicos ON medicos.id = turnos.id_medico
    WHERE turnos.estado = 'confirmado'
    AND DATE(turnos.fecha_hora) = %(fecha)s
    ORDER BY turnos.hora_checkin
    """

    return ejecutar_consulta(sql, {'fecha': fecha})


def actualizar_turno_atendido(id) -> dict | None:
    """
    Cambia el estado de un turno de "confirmado" a "atendido" y devuelve el turno actualizado.
    """

    turno = buscar_turno_id(id)

    if not turno or turno['estado'] != 'confirmado':
        return None

    sql = """
    UPDATE turnos
    SET estado = 'atendido'
    WHERE id = %(id)s AND estado = 'confirmado'
    """
    ejecutar_mutacion(sql, {'id': id})

    turno = buscar_turno_id(id)

    return turno


def marcar_turno_ausente(id) -> dict | None:
    """
    Cambia el estado de un turno de "reservado" a "ausente" y devuelve el turno actualizado.
    """

    turno = buscar_turno_id(id)

    if not turno or turno['estado'] != 'reservado':
        return None

    sql = """
    UPDATE turnos
    SET estado = 'ausente'
    WHERE id = %(id)s AND estado = 'reservado'
    """
    ejecutar_mutacion(sql, {'id': id})

    turno = buscar_turno_id(id)

    return turno
