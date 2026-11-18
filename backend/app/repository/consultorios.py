from app.db import get_connection

COLUMNAS_CONSULTORIO = "id, nombre, ubicacion, activo"


def listar():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT " + COLUMNAS_CONSULTORIO + " FROM consultorios ORDER BY nombre"
    )
    consultorios = cursor.fetchall()

    cursor.close()
    connection.close()

    return consultorios


def obtener_por_id(id_consultorio):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT " + COLUMNAS_CONSULTORIO + " FROM consultorios WHERE id = %s",
        (id_consultorio,)
    )
    consultorio = cursor.fetchone()

    cursor.close()
    connection.close()

    return consultorio


def crear(consultorio):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO consultorios (nombre, ubicacion, activo) "
        "VALUES (%s, %s, %s)",
        (
            consultorio["nombre"],
            consultorio["ubicacion"],
            consultorio["activo"]
        )
    )
    connection.commit()
    id_creado = cursor.lastrowid

    cursor.close()
    connection.close()

    return id_creado


def actualizar(id_consultorio, cambios):
    columnas = []
    valores = []

    for campo in ("nombre", "ubicacion"):
        if campo in cambios:
            columnas.append(campo + " = %s")
            valores.append(cambios[campo])

    valores.append(id_consultorio)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE consultorios SET " + ", ".join(columnas) + " WHERE id = %s",
        tuple(valores)
    )
    connection.commit()

    cursor.close()
    connection.close()


def dar_baja(id_consultorio):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE consultorios SET activo = %s WHERE id = %s",
        (0, id_consultorio)
    )
    connection.commit()

    cursor.close()
    connection.close()