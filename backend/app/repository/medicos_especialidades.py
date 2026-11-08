from app.db import get_connection


def listar():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT id, nombre FROM especialidades ORDER BY nombre")
    especialidades = cursor.fetchall()

    cursor.close()
    connection.close()

    return especialidades


def obtener_por_nombre(nombre):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, nombre FROM especialidades WHERE nombre = %s",
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
        "INSERT INTO especialidades (nombre) VALUES (%s)",
        (especialidad["nombre"],)
    )
    connection.commit()
    id_creado = cursor.lastrowid

    cursor.close()
    connection.close()

    return id_creado