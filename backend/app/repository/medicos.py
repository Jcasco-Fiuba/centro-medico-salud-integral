from app.db import ejecutar_mutacion, ejecutar_consulta

# ---------------------------------------------------------------
# Queries de medicos
# ---------------------------------------------------------------

CAMPOS_EDITABLES_MEDICO = {'nombre', 'apellido', 'matricula', 'id_consultorio'}


def listar_medicos() -> list[dict]:
    """
    Lista todos los medicos de la base de datos.
    """

    sql = """
    SELECT id, nombre, apellido, matricula, id_consultorio, activo
    FROM medicos
    JOIN medicos_especialidades ON medicos_especialidades.id_medico = medicos.id
    WHERE medicos_especialidades.id_especialidad = %(id_especialidad)s AND medicos.activo = TRUE
    ORDER BY medicos.apellido, medicos.nombre
    """
    return ejecutar_consulta(sql, {"id_especialidad": id_especialidad})


def obtener_medico_por_id(id) -> dict:
    """
    Recibe un id y muestra al medico al que le pertenece el id,
    si no existe muestra una lista vacia.
    """

    sql = """
    SELECT id, nombre, apellido, matricula, id_consultorio, activo
    FROM medicos
    WHERE id = %(id)s
    """
    filas = ejecutar_consulta(sql, {'id': id})

    return filas[0] if filas else None


def crear_medico(datos: dict) -> int:
    """
    Recibe datos del nuevo medico y lo agrega a la base de datos.
    """

    sql = """
    INSERT INTO medicos (nombre, apellido, matricula, id_consultorio)
    VALUES (%(nombre)s, %(apellido)s, %(matricula)s, %(id_consultorio)s)
    """
    return ejecutar_mutacion(sql, {
        'nombre': datos['nombre'],
        'apellido': datos['apellido'],
        'matricula': datos['matricula'],
        'id_consultorio': datos['id_consultorio']
    })


def actualizar_medico(id, campos: dict) -> dict:
    """
    Actualiza los campos recibidos del medico con el id dado y
    retorna el medico actualizado.
    """

    campos_validos = {}

    for campo, valor in campos.items():
        if campo in CAMPOS_EDITABLES_MEDICO:
            campos_validos[campo] = valor

    if not campos_validos:
        return obtener_medico_por_id(id)

    set_clause = ", ".join(f"{campo} = %({campo})s" for campo in campos_validos)
    sql = f"UPDATE medicos SET {set_clause} WHERE id = %(id)s"
    parametros = {**campos_validos, "id": id}

    ejecutar_mutacion(sql, parametros)

    return obtener_medico_por_id(id)


def dar_baja_medico(id) -> dict:
    """
    Da de baja al medico con el id seleccionado y lo retorna actualizado.
    """

    sql = "UPDATE medicos SET activo = FALSE WHERE id = %(id)s"

    ejecutar_mutacion(sql, {'id': id})

    return obtener_medico_por_id(id)


def listar_especialidades_por_medico(id_medico) -> list[dict]:
    """
    Recibe el id de un medico y devuelve sus especialidades.
    """

    sql = """
    SELECT especialidades.id, especialidades.nombre
    FROM especialidades
    INNER JOIN medicos_especialidades
        ON medicos_especialidades.id_especialidad = especialidades.id
    WHERE medicos_especialidades.id_medico = %(id_medico)s
    ORDER BY especialidades.nombre
    """
    return ejecutar_consulta(sql, {'id_medico': id_medico})


def borrar_especialidades_medico(id_medico) -> int:
    """
    Recibe el id de un medico y le quita todas sus especialidades.
    """

    sql = "DELETE FROM medicos_especialidades WHERE id_medico = %(id_medico)s"
    return ejecutar_mutacion(sql, {'id_medico': id_medico})


# ---------------------------------------------------------------
# Queries de especialidades
# ---------------------------------------------------------------

def listar_especialidades() -> list[dict]:

    """
    Lista todas las especialidades de la base de datos.
    """

    sql = """
    SELECT id, nombre
    FROM especialidades
    ORDER BY nombre
    """

    return ejecutar_consulta(sql)


def crear_especialidad(datos: dict) -> int:

    """
    Recibe datos de la nueva especialidad y la agrega a la base de datos.
    """

    sql = """
    INSERT INTO especialidades (nombre)
    VALUES (%(nombre)s)
    """
    return ejecutar_mutacion(sql, {
        'nombre': datos['nombre']
    })


def asociar_medico_especialidad(datos: dict) -> int:

    """
    Recibe el id de un medico y el id de una especialidad y asigna la especialidad
    al medico en la base de datos.
    """

    sql = """
    INSERT INTO medicos_especialidades (id_medico, id_especialidad)
    VALUES (%(id_medico)s, %(id_especialidad)s)
    """
    return ejecutar_mutacion(sql, {
        'id_medico': datos['id_medico'],
        'id_especialidad': datos['id_especialidad']
    })
