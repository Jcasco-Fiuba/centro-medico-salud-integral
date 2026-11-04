from datetime import date, datetime
import json

def validar_json(texto):
    errores= []
    try:
        datos = json.loads(texto)
    except ValueError:
        errores.append("JSON invalido")
        return None, errores

    if type(datos) != dict:
        errores.append("El JSON debe ser un diccionario")
        return None, errores

    return datos, errores

def validar_estado(estado):
    estado_valido = True
    if estado not in ("disponible", "reservado", "confirmado", "cancelado", "ausente", "atendido"):
        estado_valido = False

    return estado_valido

def validar_fecha(fecha):

    if type(fecha) != str:
        return False
    partes = fecha.split("-")
    if len(partes) != 3:
        return False

    anio, mes, dia = partes

    if len(anio) != 4 or len(mes) != 2 or len(dia) != 2:
        return False
    if not anio.isdigit() or not mes.isdigit() or not dia.isdigit():
        return False
    try:
        date(int(anio), int(mes), int(dia))
        return True
    except ValueError:
        return False

def validar_consulta_disponible (datos):
    errores= []
    if "medico" not in datos:
        errores.append("Falta el ID del medico")
    elif type(datos["medico"]) != str:
        errores.append("El ID del medico debe ser texto")
    elif not datos["medico"].isdigit():
        errores.append("El ID del medico debe ser un numero")
    elif int(datos["medico"]) <= 0:
        errores.append("El ID del medico debe ser mayor a 0")
    if "fecha" not in datos:
        errores.append("Falta la fecha")
    elif not validar_fecha(datos["fecha"]):
        errores.append("La fecha no es valida")
    return errores

def validar_get_turnos(datos):
    errores= []
    if "estado" in datos:
        if not validar_estado(datos["estado"]):
            errores.append("El estado no es valido")

    if "medico" in datos:
        if type(datos["medico"]) != str:
            errores.append("El ID del medico debe ser texto")
        elif not datos["medico"].isdigit():
            errores.append("El ID del medico debe ser un numero")
        elif int(datos["medico"]) <= 0:
            errores.append("El ID del medico debe ser mayor a 0")

    if "dni" in datos:
        if type(datos["dni"]) != str:
            errores.append("El DNI debe ser texto")
        elif len(datos["dni"]) < 7 or len(datos["dni"]) > 8:
            errores.append("El DNI no es valido")
        elif not datos["dni"].isdigit():
            errores.append("El DNI no es valido")
    return errores

def validar_fecha_hora(fecha_hora):
    if type(fecha_hora) != str:
        return False
    try:
        fecha_convertida = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
        if fecha_convertida.strftime("%Y-%m-%d %H:%M:%S") != fecha_hora:
            return False
        return True
    except ValueError:
        return False

def validar_post_turno(datos):
    errores = []

    campos = ["id_medico", "id_consultorio", "fecha_hora"]
    campos_permitidos = ["id_medico", "id_consultorio", "fecha_hora"]
    for campo in campos:
        if campo not in datos:
            errores.append("Falta el campo " + campo)

    for campo in datos:
        if campo not in campos_permitidos:
            errores.append("El campo " + campo + " no esta permitido")

    if "id_medico" in datos:
        if type(datos["id_medico"]) != int:
            errores.append("El ID del medico debe ser un numero entero")
        elif datos["id_medico"] <= 0:
            errores.append("El ID del medico debe ser mayor a 0")

    if "id_consultorio" in datos:
        if type(datos["id_consultorio"]) != int:
            errores.append("El ID del consultorio debe ser un numero entero")
        elif datos["id_consultorio"] <= 0:
            errores.append("El ID del consultorio debe ser mayor a 0")

    if "fecha_hora" in datos:
        if not validar_fecha_hora(datos["fecha_hora"]):
            errores.append("La fecha y hora no son validas")

    return errores

def validar_reserva_turno(datos):
    errores = []

    if "turno_id" not in datos:
        errores.append("Falta el ID del turno")
    elif type(datos["turno_id"]) != int:
        errores.append("El ID del turno debe ser un numero entero")
    elif datos["turno_id"] <= 0:
        errores.append("El ID del turno debe ser mayor a 0")

    return errores

def validar_checkin(datos):
    errores = []

    if "string_token" not in datos:
        errores.append("Falta string_token")
    elif type(datos["string_token"]) != str:
        errores.append("El token debe ser texto")
    elif datos["string_token"].strip() == "":
        errores.append("El token no puede estar vacio")

    return errores
