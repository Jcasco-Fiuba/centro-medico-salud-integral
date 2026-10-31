"""Servicios para el módulo de médicos."""

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
