from sqlalchemy import create_engine, text
from db.constants import (DB_URL,
                       CAMPOS_EDITABLES_PACIENTE)

# ---------------------------------------------------------------
# Funciones de soporte genéricas
# ---------------------------------------------------------------

def obtener_conexion():
    """Crea y retorna una nueva conexion a la base de datos."""
    motor = create_engine(DB_URL)
    return motor.connect()

def fila_a_dict(fila) -> dict:
    """Convierte una fila del resultado de una query en un diccionario."""
    return dict(fila._mapping)

def ejecutar_consulta(sql: str, parametros: dict = None) -> list[dict]:
    """Ejecuta una SELECT y devuelve todas las filas como lista de dicts."""
    with obtener_conexion() as conexion:
        resultado = conexion.execute(text(sql), parametros or {})
        return [fila_a_dict(fila) for fila in resultado]

def ejecutar_mutacion(sql: str, parametros: dict = None) -> int:
    """
    Ejecuta un INSERT, UPDATE o DELETE y hace commit.
    Retorna el id autoincremental generado por el INSERT (0 si no aplica).
    """
    with obtener_conexion() as conexion:
        with conexion.begin():
            resultado = conexion.execute(text(sql), parametros or {})
        return resultado.lastrowid or 0


# ---------------------------------------------------------------
# Queries de pacientes
# ---------------------------------------------------------------

def obtener_paciente_por_dni(dni: str) -> dict:

    """
    Recibe un dni y muestra al paciente al que le pertenece ese dni,
    sino muestra una lista vacía.
    """

    sql = """
        SELECT id, dni, nombre, apellido, email, activo
        FROM usuarios
        WHERE dni = :dni AND rol = 'paciente'
    """
    filas = ejecutar_consulta(sql, {'dni': dni})

    return filas[0] if filas else {}

def obtener_paciente_por_email(email: str) -> dict:

    """Recibe un email y muestra al paciente al que le pertenece ese email,
    sino muestra una lista vacía.
    """

    sql = """
        SELECT id, dni, nombre, apellido, email, activo
        FROM usuarios
        WHERE email = :email AND rol = 'paciente'
    """
    filas = ejecutar_consulta(sql, {'email': email})

    return filas[0] if filas else {}

def crear_paciente(datos: dict) -> int:

    """
    Recibe datos del paciente y lo agrega a la base de datos.
    """

    sql = """
        INSERT INTO usuarios (dni, nombre, apellido, email, password_hash, rol)
        VALUES (:dni, :nombre, :apellido, :email, :password_hash, 'paciente')
    """
    return ejecutar_mutacion(sql, {
        'dni': datos['dni'],
        'nombre': datos['nombre'],
        'apellido': datos['apellido'],
        'email': datos['email'],
        'password_hash': datos['password_hash']
    })

def actualizar_paciente(dni: str, campos: dict) -> dict:

    """
    Actualiza los campos recibidos del paciente con el dni dado y
    retorna el paciente actualizado.
    """

    campos_validos = {}
 
    for campo, valor in campos.items():
        if campo in CAMPOS_EDITABLES_PACIENTE:
            campos_validos[campo] = valor
 
    if not campos_validos:
        return obtener_paciente_por_dni(dni)
 
    set_clause = ", ".join(f"{campo} = :{campo}" for campo in campos_validos)
    sql = f"UPDATE usuarios SET {set_clause} WHERE dni = :dni AND rol = 'paciente'"
    parametros = {**campos_validos, "dni": dni}
 
    ejecutar_mutacion(sql, parametros)
 
    return obtener_paciente_por_dni(dni)


def listar_pacientes() -> list[dict]:
    sql = """
        SELECT id, dni, nombre, apellido, email, activo
        FROM usuarios
        WHERE rol = 'paciente'
        ORDER BY apellido, nombrez
    """
    return ejecutar_consulta(sql)
