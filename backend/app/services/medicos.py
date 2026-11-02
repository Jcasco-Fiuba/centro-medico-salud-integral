"""Servicios para el módulo de médicos."""

from mysql.connector import errors
from app import db




def listar_medicos():
    """Obtiene el listado de médicos desde la capa de persistencia."""
    if not hasattr(db, "listar_medicos"):
        raise NotImplementedError(
            "Falta implementar listar_medicos en la capa de base de datos."
        )

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
    return db.obtener_medico_por_id(id_medico)

 
def crear_medico(datos: dict) -> dict:
    """crea el médico y lo devuelve completo."""
    try:
        id_medico = db.crear_medico(datos)
    except errors.IntegrityError:
        raise ValueError("La matrícula ya existe, o el consultorio o alguna especialidad no existe.")

    return db.obtener_medico_por_id(id_medico)


def modificar_medico(id_medico: int, cambios: dict):
    
    """modifica el médico y lo devuelve actualizado, o None si no existe."""
    try:
        existia = db.actualizar_medico(id_medico, cambios)
    except errors.IntegrityError:
        raise ValueError("La matrícula ya existe, o el consultorio o alguna especialidad no existe.")

    if not existia:
        return None
    return db.obtener_medico_por_id(id_medico)