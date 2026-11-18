"""Logica de negocio de Especialidades: valida los datos y usa el repository."""

from app.validators.medicos_especialidades import (
    validar_id_especialidad,
    validar_registro_especialidad,
    validar_actualizacion_especialidad
)

from app.repository import medicos_especialidades as especialidades_repository


def armar_especialidad(fila):
    descripcion = ""
    if fila["descripcion"] is not None:
        descripcion = fila["descripcion"]

    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "descripcion": descripcion,
        "activo": bool(fila["activo"])
    }


def listar_especialidades():
    filas = especialidades_repository.listar()

    especialidades = []

    for fila in filas:
        especialidades.append(armar_especialidad(fila))

    return {"especialidades": especialidades}, 200


def obtener_especialidad(id_especialidad):
    if not validar_id_especialidad(id_especialidad):
        return {"error": "El ID de la especialidad no es valido"}, 400

    fila = especialidades_repository.obtener_por_id(int(id_especialidad))

    if fila is None:
        return {"error": "Especialidad no encontrada"}, 404

    return armar_especialidad(fila), 200


def registrar_especialidad(datos):
    errores = validar_registro_especialidad(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    nombre = datos["nombre"].strip()

    descripcion = None
    if "descripcion" in datos and datos["descripcion"] is not None:
        descripcion = datos["descripcion"].strip()

    if especialidades_repository.obtener_por_nombre(nombre):
        return {"error": "La especialidad ya esta registrada"}, 409

    id_creado = especialidades_repository.crear({
        "nombre": nombre,
        "descripcion": descripcion
    })

    return {
        "mensaje": "Especialidad registrada correctamente",
        "id": id_creado
    }, 201


def actualizar_especialidad(id_especialidad, datos):
    if not validar_id_especialidad(id_especialidad):
        return {"error": "El ID de la especialidad no es valido"}, 400

    errores = validar_actualizacion_especialidad(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    id_especialidad = int(id_especialidad)

    if especialidades_repository.obtener_por_id(id_especialidad) is None:
        return {"error": "Especialidad no encontrada"}, 404

    cambios = {}

    if "nombre" in datos:
        nombre = datos["nombre"].strip()
        existente = especialidades_repository.obtener_por_nombre(nombre)

        if existente and existente["id"] != id_especialidad:
            return {"error": "Ya existe otra especialidad con ese nombre"}, 409

        cambios["nombre"] = nombre

    if "descripcion" in datos:
        if datos["descripcion"] is None:
            cambios["descripcion"] = None
        else:
            cambios["descripcion"] = datos["descripcion"].strip()

    if "activo" in datos:
        cambios["activo"] = datos["activo"]

    especialidades_repository.actualizar(id_especialidad, cambios)

    fila = especialidades_repository.obtener_por_id(id_especialidad)

    return armar_especialidad(fila), 200
