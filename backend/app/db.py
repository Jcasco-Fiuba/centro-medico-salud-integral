from sqlalchemy import create_engine, text
from .constants import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# ---------------------------------------------------------------
# Funciones de soporte genéricas
# ---------------------------------------------------------------

DB_URL = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

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

CAMPOS_EDITABLES_PACIENTE = {'nombre', 'apellido', 'email', 'password_hash', 'activo'}

def listar_pacientes() -> list[dict]:

    """
    Lista todos los pacientes de la base de datos
    """

    sql = """
    SELECT id, dni, nombre, apellido, email, activo
    FROM usuarios
    WHERE rol = 'paciente'
    ORDER BY apellido, nombre
    """
    return ejecutar_consulta(sql)


def obtener_paciente_por_dni(dni) -> dict:

    """
    Recibe un dni y muestra al paciente al que le pertenece el dni,
    sino muestra una lista vacia.
    """

    sql = """
    SELECT id, dni, nombre, apellido, email, activo
    FROM usuarios
    WHERE dni = :dni AND rol = 'paciente'
    """
    filas = ejecutar_consulta(sql, {'dni': dni})

    return filas[0] if filas else {}


def obtener_paciente_por_email(email) -> dict:

    """
    Recibe un email y muestra al paciente al que le pertenece ese email,
    sino muestra una lista vacia.
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
    Recibe datos del nuevo paciente y lo agrega a la base de datos.
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


def actualizar_paciente(dni, campos: dict) -> dict:

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


def baja_paciente(dni) -> dict:

    """
    Da de baja al paciente con el dni seleccionado y lo retorna actualizado.
    """

    sql = "UPDATE usuarios SET activo = FALSE WHERE dni = :dni AND rol = 'paciente'"
 
    ejecutar_mutacion(sql, {'dni': dni})
 
    return obtener_paciente_por_dni(dni)

# ---------------------------------------------------------------
# Queries de medicos
# ---------------------------------------------------------------

CAMPOS_EDITABLES_MEDICO = {'nombre', 'apellido', 'id_consultorio'}

def listar_medicos() -> list[dict]:

    """
    Lista todos los medicos de la base de datos.
    """

    sql = """
    SELECT id, nombre, apellido, matricula, id_consultorio, activo
    FROM medicos
    ORDER BY apellido, nombre
    """
    return ejecutar_consulta(sql)


def obtener_medico_por_id(id) -> dict:

    """
    Recibe un id y muestra al medico al que le pertenece el id,
    si no existe muestra una lista vacia.
    """

    sql = """
    SELECT id, nombre, apellido, matricula, id_consultorio, activo
    FROM medicos
    WHERE id = :id
    """
    filas = ejecutar_consulta(sql, {'id': id})

    return filas[0] if filas else {}


def crear_medico(datos: dict) -> int:

    """
    Recibe datos del nuevo medico y lo agrega a la base de datos.
    """

    sql = """
    INSERT INTO medicos (nombre, apellido, matricula, id_consultorio)
    VALUES (:nombre, :apellido, :matricula, :id_consultorio)
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
 
    set_clause = ", ".join(f"{campo} = :{campo}" for campo in campos_validos)
    sql = f"UPDATE medicos SET {set_clause} WHERE id = :id"
    parametros = {**campos_validos, "id": id}
 
    ejecutar_mutacion(sql, parametros)
 
    return obtener_medico_por_id(id)


def baja_medico(id) -> dict:

    """
    Da de baja al medico con el id seleccionado y lo retorna actualizado.
    """

    sql = "UPDATE medicos SET activo = FALSE WHERE id = :id"
 
    ejecutar_mutacion(sql, {'id': id})
 
    return obtener_medico_por_id(id)

# ---------------------------------------------------------------
# Queries de turnos
# ---------------------------------------------------------------

def listar_turnos() -> list[dict]:

    """
    Lista todos los turnos disponibles.
    """

    sql = """
    SELECT id_medico, id_consultorio, fecha_hora
    FROM turnos
    WHERE estado = 'disponible'
    """
    return ejecutar_consulta(sql)


def buscar_turno_id(id):
    
    """
    Recibe un id de turno y retorna el detalle del mismo.
    """

    sql = """
    SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado, string_token
    FROM turnos
    WHERE id = :id
    """  
    filas = ejecutar_consulta(sql, {'id': id})
    
    return filas[0] if filas else {}


def buscar_turno_por_medico(medico, estado) -> list[dict]:

    """
    Recibe el id de un medico y un estado, y lista los turnos
    del medico con el estado seleccionados.
    """

    sql = """
    SELECT id, id_usuario, id_medico, id_consultorio, fecha_hora, estado
    FROM turnos
    WHERE id_medico = :medico AND estado = :estado
    """

    return ejecutar_consulta(sql, {'medico': medico, 'estado': estado})


def crear_turno(datos: dict) -> dict:

    """
    Recibe datos del nuevo turno y lo agrega a la base de datos.
    """

    sql = """
    INSERT INTO turnos (id_medico, id_consultorio, fecha_hora)
    VALUES (:id_medico, :id_consultorio, :fecha_hora)
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
    SET id_usuario = :usuario_id, string_token = :token, estado = 'reservado'
    WHERE id = :turno_id AND estado = 'disponible'
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