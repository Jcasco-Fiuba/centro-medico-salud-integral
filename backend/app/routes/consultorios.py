"""Rutas y endpoints para la entidad Consultorios."""

from app.validators.consultorios import (
    validar_id_consultorio,
    validar_registro_consultorio,
    validar_actualizacion_consultorio
)

from app.repository import consultorios as consultorios_repository


def armar_consultorio(fila):
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "ubicacion": fila["ubicacion"],
        "activo": bool(fila["activo"])
    }


def listar_consultorios():
    filas = consultorios_repository.listar()

    consultorios = []

    for fila in filas:
        consultorios.append(armar_consultorio(fila))

    return {"consultorios": consultorios}, 200


def obtener_consultorio(id_consultorio):
    if not validar_id_consultorio(id_consultorio):
        return {"error": "El ID del consultorio no es valido"}, 400

    id_consultorio = int(id_consultorio)

    consultorio = consultorios_repository.obtener_por_id(id_consultorio)

    if not consultorio:
        return {"error": "Consultorio no encontrado"}, 404

    return {"consultorio": armar_consultorio(consultorio)}, 200


def registrar_consultorio(datos):
    errores = validar_registro_consultorio(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    nuevo_consultorio = {
        "nombre": datos["nombre"].strip(),
        "ubicacion": datos["ubicacion"].strip(),
        "activo": True
    }

    id_creado = consultorios_repository.crear(nuevo_consultorio)

    return {
        "mensaje": "Consultorio registrado correctamente",
        "id": id_creado
    }, 201


def actualizar_consultorio(id_consultorio, datos):
    if not validar_id_consultorio(id_consultorio):
        return {"error": "El ID del consultorio no es valido"}, 400

    id_consultorio = int(id_consultorio)

    errores = validar_actualizacion_consultorio(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    consultorio = consultorios_repository.obtener_por_id(id_consultorio)

    if not consultorio:
        return {"error": "Consultorio no encontrado"}, 404

    cambios = {}

    for campo in datos:
        cambios[campo] = datos[campo].strip()

    consultorios_repository.actualizar(id_consultorio, cambios)

    return {
        "mensaje": "Consultorio actualizado correctamente"
    }, 200


def dar_de_baja_consultorio(id_consultorio):
    if not validar_id_consultorio(id_consultorio):
        return {"error": "El ID del consultorio no es valido"}, 400

    id_consultorio = int(id_consultorio)

    consultorio = consultorios_repository.obtener_por_id(id_consultorio)

    if not consultorio:
        return {"error": "Consultorio no encontrado"}, 404

    if not consultorio["activo"]:
        return {"error": "El consultorio ya esta dado de baja"}, 409

    consultorios_repository.dar_baja(id_consultorio)

    return {
        "mensaje": "Consultorio dado de baja correctamente"
    }, 200