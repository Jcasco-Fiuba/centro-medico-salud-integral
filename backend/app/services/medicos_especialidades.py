from app.validators.medicos_especialidades import validar_registro_especialidad
from app.repository import medicos_especialidades as especialidades_repository


def listar_especialidades():
    especialidades = especialidades_repository.listar()
    return {"especialidades": especialidades}, 200


def registrar_especialidad(datos):
    errores = validar_registro_especialidad(datos)

    if len(errores) > 0:
        return {"errores": errores}, 400

    nombre = datos["nombre"].strip()

    if especialidades_repository.obtener_por_nombre(nombre):
        return {"error": "La especialidad ya esta registrada"}, 409

    id_creado = especialidades_repository.crear({"nombre": nombre})

    return {
        "mensaje": "Especialidad registrada correctamente",
        "id": id_creado
    }, 201