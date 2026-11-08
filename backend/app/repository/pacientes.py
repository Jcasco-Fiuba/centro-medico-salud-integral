from app.db import get_connection

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