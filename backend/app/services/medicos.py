"""Servicios para el módulo de médicos."""

from mysql.connector import errors
from app.repository import medicos as db




def listar_medicos(id_especialidad=None):
    """Obtiene el listado de médico. Si llega una especialidad, solo devuelve los de esa especialidad."""
    if id_especialidad is not None:
        return db.listar_medicos_por_especialidad(id_especialidad)
        
    return db.listar_medicos()


def dar_de_baja_medico(id_medico: int):
    """Solicita a la capa de persistencia dar de baja al médico indicado."""
    if not hasattr(db, "dar_baja_medico"):
        raise NotImplementedError(
            "Falta implementar dar_baja_medico en la capa de base de datos."
        )

    return db.dar_baja_medico(id_medico)

def obtener_medico(id_medico: int):
    """devuelve el médico con sus especialidades, o None si no existe."""
    medico = db.obtener_medico_por_id(id_medico)
    if medico is None:
        return None

    medico["especialidades"] = db.listar_especialidades_por_medico(id_medico)
    return medico


def crear_medico(datos: dict) -> dict:
    """crea el médico , lo asocia a su/s especialidad/es y lo devuelve completo."""
    try:
        id_medico = db.crear_medico(datos)
        for id_especialidad in datos["especialidades"]:
            db.asociar_medico_especialidad({
                "id_medico": id_medico,
                "id_especialidad": id_especialidad
            })
    except errors.IntegrityError:
        raise ValueError("La matrícula ya existe, o el consultorio o alguna especialidad no existe.")

    return db.obtener_medico_por_id(id_medico)


def modificar_medico(id_medico: int, cambios: dict):
    
    """modifica el médico y lo devuelve actualizado, o None si no existe."""
    if not db.obtener_medico_por_id(id_medico):
        return None
    try:
        db.actualizar_medico(id_medico, cambios)
        if "especialidades" in cambios:
            db.borrar_especialidades_medico(id_medico)
            for id_especialidad in cambios["especialidades"]:
                db.asociar_medico_especialidad({
                    "id_medico": id_medico,
                    "id_especialidad": id_especialidad,
                })
    except errors.IntegrityError:
        raise ValueError("El consultorio o alguna especialidad no existe.")

    return obtener_medico(id_medico)
