from app.validators.consultorios import (
    validar_id_consultorio,
    validar_registro_consultorio,
    validar_actualizacion_consultorio
)

from app.db import (
    listar_consultorios as listar_consultorios_db,
    obtener_consultorio_por_id,
    crear_consultorio,
    actualizar_consultorio as actualizar_consultorio_db,
    baja_consultorio as baja_consultorio_db
)


def listar_consultorios():
    consultorios = listar_consultorios_db()
    return {"consultorios": consultorios}, 200


def obtener_consultorio(id_consultorio):
    if not validar_id_consultorio(id_consultorio):
        return {"error": "El ID del consultorio no es valido"}, 400

    consultorio = obtener_consultorio_por_id(int(id_consultorio))

    if not consultorio:
        return {"error": "Consultorio no encontrado"}, 404

    return {"consultorio": consultorio}, 200


def registrar_consultorio(datos):
    errores = validar_registro_consultorio(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    nuevo_consultorio = {
        "nombre": datos["nombre"],
        "ubicacion": datos["ubicacion"],
        "activo": True
    }

    id_creado = crear_consultorio(nuevo_consultorio)

    return {
        "mensaje": "Consultorio registrado correctamente",
        "id": id_creado
    }, 201


def actualizar_consultorio(id_consultorio, datos):
    if not validar_id_consultorio(id_consultorio):
        return {"error": "El ID del consultorio no es valido"}, 400

    errores = validar_actualizacion_consultorio(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    consultorio = obtener_consultorio_por_id(int(id_consultorio))

    if not consultorio:
        return {"error": "Consultorio no encontrado"}, 404

    actualizado = actualizar_consultorio_db(int(id_consultorio), datos)

    if not actualizado:
        return {"error": "No se pudo actualizar el consultorio"}, 404

    return {
        "mensaje": "Consultorio actualizado correctamente"
    }, 200


def dar_de_baja_consultorio(id_consultorio):
    if not validar_id_consultorio(id_consultorio):
        return {"error": "El ID del consultorio no es valido"}, 400

    consultorio = obtener_consultorio_por_id(int(id_consultorio))

    if not consultorio:
        return {"error": "Consultorio no encontrado"}, 404

    baja_consultorio_db(int(id_consultorio))

    return {
        "mensaje": "Consultorio dado de baja correctamente"
    }, 200
