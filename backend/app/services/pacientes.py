
from app.validators.pacientes import (
    validar_dni,
    validar_registro_paciente,
    validar_actualizacion_paciente
)

from app.db import (
    obtener_paciente_por_dni,
    obtener_paciente_por_email,
    crear_paciente,
    actualizar_paciente as actualizar_paciente_db
)


def obtener_paciente(dni):
    if not validar_dni(dni):
        return {"error": "El DNI no es valido"}, 400

    paciente = obtener_paciente_por_dni(dni)

    if paciente is None:
        return {"error": "Paciente no encontrado"}, 404

    datos_paciente = {
        "dni": paciente["dni"],
        "nombre": paciente["nombre"],
        "apellido": paciente["apellido"],
        "email": paciente["email"]
    }

    return {"paciente": datos_paciente}, 200


def registrar_paciente(datos):
    errores = validar_registro_paciente(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    dni = datos["dni"]
    email = datos["email"]

    if obtener_paciente_por_dni(dni) is not None:
        return {"error": "El DNI ya esta registrado"}, 409

    if obtener_paciente_por_email(email) is not None:
        return {"error": "El email ya esta registrado"}, 409

    nuevo_paciente = {
        "dni": dni,
        "nombre": datos["nombre"],
        "apellido": datos["apellido"],
        "email": email,
        "activo": True
    }

    paciente = crear_paciente(nuevo_paciente)

    datos_paciente = {
        "dni": paciente["dni"],
        "nombre": paciente["nombre"],
        "apellido": paciente["apellido"],
        "email": paciente["email"]
    }

    return {
        "mensaje": "Paciente registrado correctamente",
        "paciente": datos_paciente
    }, 201


def actualizar_paciente(dni, datos):
    if not validar_dni(dni):
        return {"error": "El DNI no es valido"}, 400

    errores = validar_actualizacion_paciente(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    paciente = obtener_paciente_por_dni(dni)

    if paciente is None:
        return {"error": "Paciente no encontrado"}, 404

    if "email" in datos:
        usuario = obtener_paciente_por_email(datos["email"])

        if usuario is not None and usuario["dni"] != dni:
            return {"error": "El email ya esta registrado"}, 409

    actualizado = actualizar_paciente_db(dni, datos)

    if not actualizado:
        return {"error": "No se pudo actualizar el paciente"}, 404

    return {
        "mensaje": "Paciente actualizado correctamente"
    }, 200
