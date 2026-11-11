"""Servicios para el módulo de médicos."""

from mysql.connector import errors

from app.repository import medicos as db


def listar_medicos() -> list[dict]:
    """Obtiene el listado de médicos desde la capa de persistencia."""
    return db.listar_medicos()


def listar_medicos_por_especialidad(id_especialidad: int) -> list[dict]:
    """Lista los médicos activos asociados a una especialidad."""
    return db.listar_medicos_por_especialidad(id_especialidad)


def dar_de_baja_medico(id_medico: int) -> dict | None:
    """Solicita a la capa de persistencia dar de baja al médico indicado."""
    if not db.obtener_medico_por_id(id_medico):
        return None
    return db.dar_baja_medico(id_medico)


def obtener_medico(id_medico: int) -> dict | None:
    """Devuelve el médico con sus especialidades, o `None` si no existe."""
    medico = db.obtener_medico_por_id(id_medico)
    if medico is None:
        return None
    medico["especialidades"] = db.listar_especialidades_por_medico(id_medico)
    return medico


def crear_medico(datos: dict) -> dict | None:
    """Crea el médico con sus especialidades transaccionalmente y lo devuelve completo."""
    try:
        id_medico = db.crear_medico(datos)
    except errors.IntegrityError as exc:
        raise ValueError(
            "La matrícula ya existe, o el consultorio o alguna especialidad no existe."
        ) from exc

    return obtener_medico(id_medico)


def modificar_medico(id_medico: int, cambios: dict) -> dict | None:
    """Modifica el médico y lo devuelve actualizado, o `None` si no existe."""
    if not db.obtener_medico_por_id(id_medico):
        return None
    try:
        db.actualizar_medico(id_medico, cambios)
        if "especialidades" in cambios:
            db.borrar_especialidades_medico(id_medico)
            for id_especialidad in cambios["especialidades"]:
                db.asociar_medico_especialidad(
                    {
                        "id_medico": id_medico,
                        "id_especialidad": id_especialidad,
                    }
                )
    except errors.IntegrityError as exc:
        raise ValueError("El consultorio o alguna especialidad no existe.") from exc

    return obtener_medico(id_medico)
