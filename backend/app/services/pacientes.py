import hashlib
import os

from app.validators.pacientes import (
    validar_dni,
    validar_registro_paciente,
    validar_actualizacion_paciente,
    validar_baja_paciente
)

from app.repository import pacientes as pacientes_repository


def generar_password_hash(password):

    sal = os.urandom(16).hex()
    hash_hex = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(sal), 100000
    ).hex()

    return sal + "$" + hash_hex


def obtener_paciente(dni):
    try:
        validar_dni(dni)
    except ValueError as error:
        return {"error": str(error)}, 400

    paciente = pacientes_repository.obtener_por_dni(dni)

    if paciente is None:
        return {"error": "Paciente no encontrado"}, 404

    datos_paciente = {
        "dni": paciente["dni"],
        "nombre": paciente["nombre"],
        "apellido": paciente["apellido"],
        "email": paciente["email"]
    }

    return {"paciente": datos_paciente}, 200


def listar_pacientes():
    filas = pacientes_repository.listar()

    pacientes = []

    for fila in filas:
        pacientes.append({
            "dni": fila["dni"],
            "nombre": fila["nombre"],
            "apellido": fila["apellido"],
            "email": fila["email"],
            "activo": bool(fila["activo"])
        })

    return {"pacientes": pacientes}, 200


def registrar_paciente(datos):
    errores = validar_registro_paciente(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    dni = datos["dni"]
    email = datos["email"]

    if pacientes_repository.obtener_por_dni(dni) is not None:
        return {"error": "El DNI ya esta registrado"}, 409

    if pacientes_repository.obtener_por_email(email) is not None:
        return {"error": "El email ya esta registrado"}, 409

    nuevo_paciente = {
        "dni": dni,
        "nombre": datos["nombre"],
        "apellido": datos["apellido"],
        "email": email,
        "password_hash": generar_password_hash(datos["password"]),
        "activo": True
    }

    paciente = pacientes_repository.crear(nuevo_paciente)

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
    try:
        validar_dni(dni)
    except ValueError as error:
        return {"error": str(error)}, 400

    errores = validar_actualizacion_paciente(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    paciente = pacientes_repository.obtener_por_dni(dni)

    if paciente is None:
        return {"error": "Paciente no encontrado"}, 404

    if "email" in datos:
        usuario = pacientes_repository.obtener_por_email(datos["email"])

        if usuario is not None and usuario["dni"] != dni:
            return {"error": "El email ya esta registrado"}, 409

    pacientes_repository.actualizar(dni, datos)

    return {
        "mensaje": "Paciente actualizado correctamente"
    }, 200


def dar_baja_paciente(dni):
    errores = validar_baja_paciente(dni)

    if len(errores) > 0:
        return {"errores": errores}, 400

    paciente = pacientes_repository.obtener_por_dni(dni)

    if paciente is None:
        return {"error": "Paciente no encontrado"}, 404

    if not paciente["activo"]:
        return {"error": "El paciente ya esta dado de baja"}, 409

    pacientes_repository.dar_baja(dni)

    return {
        "mensaje": "Paciente dado de baja correctamente"
    }, 200