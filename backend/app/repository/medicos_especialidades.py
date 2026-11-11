from app.db import get_connection

COLUMNAS_ESPECIALIDAD = "id, nombre, descripcion, activo"


def listar():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT " + COLUMNAS_ESPECIALIDAD + " FROM especialidades ORDER BY nombre"
    )
    especialidades = cursor.fetchall()

    cursor.close()
    connection.close()

    return especialidades


def obtener_por_id(id_especialidad):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT " + COLUMNAS_ESPECIALIDAD + " FROM especialidades WHERE id = %s",
        (id_especialidad,)
    )
    especialidad = cursor.fetchone()

    cursor.close()
    connection.close()

    return especialidad


def obtener_por_nombre(nombre):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT " + COLUMNAS_ESPECIALIDAD + " FROM especialidades WHERE nombre = %s",
        (nombre,)
    )
    especialidad = cursor.fetchone()

    cursor.close()
    connection.close()

    return especialidad


def crear(especialidad):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO especialidades (nombre, descripcion) VALUES (%s, %s)",
        (especialidad["nombre"], especialidad["descripcion"])
    )
    connection.commit()
    id_creado = cursor.lastrowid

    cursor.close()
    connection.close()

    return id_creado


def actualizar(id_especialidad, cambios):
    columnas = []
    valores = []

    for campo in ("nombre", "descripcion", "activo"):
        if campo in cambios:
            columnas.append(campo + " = %s")
            valores.append(cambios[campo])

    valores.append(id_especialidad)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE especialidades SET " + ", ".join(columnas) + " WHERE id = %s",
        tuple(valores)
    )
    connection.commit()

    cursor.close()
    connection.close()
