def validar_id_consultorio(id_consultorio):
    try:
        id_num = int(id_consultorio)
        return id_num > 0
    except (ValueError, TypeError):
        return False


def validar_registro_consultorio(datos):
    errores = []

    if not datos:
        errores.append("No se enviaron datos")
        return errores

    if "nombre" not in datos or not str(datos["nombre"]).strip():
        errores.append("El nombre es obligatorio")

    if "ubicacion" not in datos or not str(datos["ubicacion"]).strip():
        errores.append("La ubicacion es obligatoria")

    return errores


def validar_actualizacion_consultorio(datos):
    errores = []

    if not datos:
        errores.append("No se enviaron datos para actualizar")
        return errores

    if "nombre" in datos and not str(datos["nombre"]).strip():
        errores.append("El nombre no puede estar vacio")

    if "ubicacion" in datos and not str(datos["ubicacion"]).strip():
        errores.append("La ubicacion no puede estar vacia")

    return errores
