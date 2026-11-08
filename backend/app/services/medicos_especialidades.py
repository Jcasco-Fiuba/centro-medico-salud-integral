from app.validators.medicos_especialidades import validar_registro_especialidad
from app.db import (
    listar_especialidades as listar_especialidades_db,
    obtener_especialidad_por_nombre,
    crear_especialidad
)


def listar_especialidades():
    especialidades = listar_especialidades_db()
    return {"especialidades": especialidades}, 200


def registrar_especialidad(datos):
    errores = validar_registro_especialidad(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    nombre = datos["nombre"].strip()

    if obtener_especialidad_por_nombre(nombre):
        return {"error": "La especialidad ya esta registrada"}, 409

    id_creado = crear_especialidad({"nombre": nombre})

    return {
        "mensaje": "Especialidad registrada correctamente",
        "id": id_creado
    }, 201