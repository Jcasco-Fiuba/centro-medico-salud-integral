from app.db import get_connection


def listar():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT dni, nombre, apellido, email, activo "
        "FROM usuarios WHERE rol = %s ORDER BY apellido, nombre",
        ("paciente",)
    )
    pacientes = cursor.fetchall()
    cursor.close()
    connection.close()
    return pacientes


def obtener_por_dni(dni):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT dni, nombre, apellido, email, activo "
        "FROM usuarios WHERE dni = %s AND rol = %s",
        (dni, "paciente")
    )
    paciente = cursor.fetchone()
    cursor.close()
    connection.close()
    return paciente


def obtener_por_email(email):
    # Sin filtrar por rol: usuarios.email es UNIQUE para todos los usuarios.
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT dni, nombre, apellido, email, activo "
        "FROM usuarios WHERE email = %s",
        (email,)
    )
    usuario = cursor.fetchone()
    cursor.close()
    connection.close()
    return usuario


def crear(paciente):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "INSERT INTO usuarios "
        "(dni, nombre, apellido, email, password_hash, rol, activo) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            paciente["dni"],
            paciente["nombre"],
            paciente["apellido"],
            paciente["email"],
            paciente["password_hash"],
            "paciente",
            paciente["activo"]
        )
    )
    connection.commit()
    cursor.execute(
        "SELECT dni, nombre, apellido, email, activo "
        "FROM usuarios WHERE dni = %s AND rol = %s",
        (paciente["dni"], "paciente")
    )
    creado = cursor.fetchone()
    cursor.close()
    connection.close()
    return creado


def actualizar(dni, datos):
    # Los nombres de columna salen de esta lista fija, no del request.
    columnas = []
    valores = []
    for campo in ("nombre", "apellido", "email"):
        if campo in datos:
            columnas.append(campo + " = %s")
            valores.append(datos[campo])
    valores.append(dni)
    valores.append("paciente")
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE usuarios SET " + ", ".join(columnas) + " "
        "WHERE dni = %s AND rol = %s",
        tuple(valores)
    )
    connection.commit()
    cursor.close()
    connection.close()


def dar_baja(dni):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE usuarios SET activo = %s WHERE dni = %s AND rol = %s",
        (0, dni, "paciente")
    )
    connection.commit()
    modificadas = cursor.rowcount
    cursor.close()
    connection.close()
    return modificadas > 0