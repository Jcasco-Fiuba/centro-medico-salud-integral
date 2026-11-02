def validar_registro_especialidad(datos):
    errores = []

    if not datos:
        errores.append("No se enviaron datos")
        return errores

    if "nombre" not in datos or not str(datos["nombre"]).strip():
        errores.append("El nombre de la especialidad es obligatorio")

    return errores
