"""Validadores para el módulo de médicos."""


def validar_id_medico(id_valor: str) -> int:
    """Valida que el ID recibido en la ruta sea un entero positivo."""
    if not id_valor.isdigit() or int(id_valor) <= 0:
        raise ValueError("El ID del médico debe ser un entero positivo.")

    return int(id_valor)
