"""Validadores para el módulo de médicos."""

CAMPOS_TEXTO_MEDICO = ("nombre", "apellido", "matricula")


def validar_id_medico(id_valor: str) -> int:
    """Valida que el ID recibido en la ruta sea un entero positivo."""
    if not isinstance(id_valor, str) or not (id_valor.isascii() and id_valor.isdigit()) or int(id_valor) <= 0:
        raise ValueError("El ID del médico debe ser un entero positivo.")

    return int(id_valor)

def validar_alta_medico(datos) -> dict:
    """Valida el body del POST y devuelve los datos limpios."""
    if not isinstance(datos, dict):
        raise ValueError("El cuerpo de la petición debe ser un JSON.")

    medico = {}
    for campo in CAMPOS_TEXTO_MEDICO:
        if not _es_texto(datos.get(campo)):
            raise ValueError(f"El campo '{campo}' es obligatorio.")
        medico[campo] = datos[campo].strip()

    if not _es_entero_positivo(datos.get("id_consultorio")):
        raise ValueError("El campo 'id_consultorio' debe ser un entero positivo.")
    medico["id_consultorio"] = datos["id_consultorio"]

    if not _es_lista_de_ids(datos.get("especialidades")):
        raise ValueError("El campo 'especialidades' debe ser una lista de IDs.")
    medico["especialidades"] = list(set(datos["especialidades"]))

    return medico


def validar_modificacion_medico(datos) -> dict:
    """Valida el body del PATCH. Todos los campos son opcionales, pero tiene
    que venir al menos uno. Devuelve solo los campos enviados, limpios."""
    if not isinstance(datos, dict):
        raise ValueError("El cuerpo de la petición debe ser un JSON.")

    cambios = {}
    for campo in CAMPOS_TEXTO_MEDICO:
        if campo in datos:
            if not _es_texto(datos[campo]):
                raise ValueError(f"El campo '{campo}' no puede estar vacío.")
            cambios[campo] = datos[campo].strip()

    if "id_consultorio" in datos:
        if not _es_entero_positivo(datos["id_consultorio"]):
            raise ValueError("El campo 'id_consultorio' debe ser un entero positivo.")
        cambios["id_consultorio"] = datos["id_consultorio"]

    if "especialidades" in datos:
        if not _es_lista_de_ids(datos["especialidades"]):
            raise ValueError("El campo 'especialidades' debe ser una lista de IDs.")
        cambios["especialidades"] = list(set(datos["especialidades"]))

    if not cambios:
        raise ValueError("No se envió ningún campo para modificar.")

    return cambios


def _es_texto(valor) -> bool:
    return isinstance(valor, str) and valor.strip() != ""


def _es_entero_positivo(valor) -> bool: # funciones solo para validators :)
    # True es un int (vale 1): por eso se excluyen los bool.
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def _es_lista_de_ids(valor) -> bool:
    return (
        isinstance(valor, list)
        and len(valor) > 0
        and all(_es_entero_positivo(item) for item in valor)
    )
