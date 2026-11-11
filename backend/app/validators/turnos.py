"""Validadores para el módulo de turnos."""

from datetime import date, datetime
import json


def validar_json(texto: str):
    """Valida y parsea un texto JSON en diccionario."""
    errores = []
    try:
        datos = json.loads(texto)
    except (ValueError, TypeError):
        errores.append("JSON invalido")
        return None, errores

    if not isinstance(datos, dict):
        errores.append("El JSON debe ser un diccionario")
        return None, errores

    return datos, errores


def _es_entero_positivo(valor) -> bool:
    """Devuelve True si `valor` es un entero estricto positivo (excluye booleanos)."""
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def validar_id_turno(id_turno) -> bool:
    """Valida que un ID de turno sea un entero positivo (sin booleanos ni decimales)."""
    if _es_entero_positivo(id_turno):
        return True
    if isinstance(id_turno, str):
        texto = id_turno.strip()
        return texto.isascii() and texto.isdigit() and int(texto) > 0
    return False


def validar_estado(estado: str) -> bool:
    """Valida si el estado pertenece a los estados de turno permitidos."""
    estados_validos = (
        "disponible",
        "reservado",
        "confirmado",
        "cancelado",
        "ausente",
        "atendido",
    )
    return estado in estados_validos


def validar_fecha(fecha: str) -> bool:
    """Valida que la fecha tenga formato YYYY-MM-DD y sea una fecha de calendario válida."""
    if not isinstance(fecha, str):
        return False
    partes = fecha.split("-")
    if len(partes) != 3:
        return False

    anio, mes, dia = partes
    if len(anio) != 4 or len(mes) != 2 or len(dia) != 2:
        return False
    if not (anio.isascii() and anio.isdigit() and mes.isascii() and mes.isdigit() and dia.isascii() and dia.isdigit()):
        return False

    try:
        date(int(anio), int(mes), int(dia))
        return True
    except ValueError:
        return False


def validar_fecha_hora(fecha_hora) -> bool:
    """Valida que fecha_hora sea un string con formato fecha y hora válido."""
    if not isinstance(fecha_hora, str):
        return False
    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]
    for fmt in formatos:
        try:
            datetime.strptime(fecha_hora, fmt)
            return True
        except ValueError:
            continue
    return False


def validar_consulta_disponible(datos) -> list[str]:
    """Valida los parámetros de consulta de turnos disponibles (médico y fecha)."""
    errores = []
    if not isinstance(datos, dict):
        return ["Los parámetros deben ser un objeto"]

    if "medico" not in datos or datos["medico"] is None:
        errores.append("Falta el ID del medico")
    else:
        medico_str = str(datos["medico"])
        if not (medico_str.isascii() and medico_str.isdigit()):
            errores.append("El ID del medico debe ser un numero")
        elif int(medico_str) <= 0:
            errores.append("El ID del medico debe ser mayor a 0")

    if "fecha" not in datos or not datos["fecha"]:
        errores.append("Falta la fecha")
    elif not validar_fecha(str(datos["fecha"])):
        errores.append("La fecha no es valida")

    return errores


def validar_get_turnos(datos) -> list[str]:
    """Valida filtros opcionales para listar turnos (estado, médico, DNI)."""
    errores = []
    if not isinstance(datos, dict):
        return ["Los parámetros deben ser un objeto"]

    if "estado" in datos and datos["estado"] is not None:
        if not validar_estado(str(datos["estado"])):
            errores.append("El estado no es valido")

    if "medico" in datos and datos["medico"] is not None:
        medico_str = str(datos["medico"])
        if not (medico_str.isascii() and medico_str.isdigit()):
            errores.append("El ID del medico debe ser un numero")
        elif int(medico_str) <= 0:
            errores.append("El ID del medico debe ser mayor a 0")

    if "dni" in datos and datos["dni"] is not None:
        dni_str = str(datos["dni"])
        if len(dni_str) < 7 or len(dni_str) > 8 or not (dni_str.isascii() and dni_str.isdigit()):
            errores.append("El DNI no es valido")

    return errores


def validar_post_turno(datos) -> list[str]:
    """Valida los campos requeridos para la creación de un nuevo turno disponible."""
    errores = []
    if not isinstance(datos, dict):
        return ["El cuerpo debe ser un objeto JSON"]

    campos_requeridos = ["id_medico", "id_consultorio", "fecha_hora"]
    for campo in campos_requeridos:
        if campo not in datos or datos[campo] is None:
            errores.append("Falta el campo " + campo)

    for campo in datos:
        if campo not in campos_requeridos:
            errores.append("El campo " + campo + " no esta permitido")

    if "id_medico" in datos and datos["id_medico"] is not None:
        if not _es_entero_positivo(datos["id_medico"]):
            errores.append("El ID del medico debe ser un numero entero mayor a 0")

    if "id_consultorio" in datos and datos["id_consultorio"] is not None:
        if not _es_entero_positivo(datos["id_consultorio"]):
            errores.append("El ID del consultorio debe ser un numero entero mayor a 0")

    if "fecha_hora" in datos and datos["fecha_hora"] is not None:
        if not validar_fecha_hora(datos["fecha_hora"]):
            errores.append("La fecha y hora no son validas")

    return errores


def validar_reserva_turno(datos) -> list[str]:
    """Valida los datos requeridos para reservar un turno."""
    errores = []
    if not isinstance(datos, dict):
        return ["El cuerpo debe ser un objeto JSON"]

    if "turno_id" not in datos or datos["turno_id"] is None:
        errores.append("Falta el ID del turno")
    elif not _es_entero_positivo(datos["turno_id"]):
        errores.append("El ID del turno debe ser un numero entero mayor a 0")

    return errores


def validar_checkin(datos) -> list[str]:
    """Valida los datos para realizar check-in con token QR."""
    errores = []
    if not isinstance(datos, dict):
        return ["El cuerpo debe ser un objeto JSON"]

    if "string_token" not in datos or datos["string_token"] is None:
        errores.append("Falta string_token")
    elif not isinstance(datos["string_token"], str) or not datos["string_token"].strip():
        errores.append("El token no puede estar vacio")

    return errores
