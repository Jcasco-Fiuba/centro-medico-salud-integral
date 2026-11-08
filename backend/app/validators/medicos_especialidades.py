def validar_registro_especialidad(datos):
    errores = []

    if not datos:
        errores.append("No se enviaron datos")
        return errores

    if type(datos) != dict:
        errores.append("Los datos deben ser un objeto")
        return errores

    if "nombre" not in datos:
        errores.append("El nombre de la especialidad es obligatorio")
    elif type(datos["nombre"]) != str:
        errores.append("El nombre de la especialidad debe ser texto")
    elif len(datos["nombre"].strip()) == 0:
        errores.append("El nombre de la especialidad es obligatorio")
    elif len(datos["nombre"].strip()) > 50:
        errores.append("El nombre de la especialidad no puede superar los 50 caracteres")

    return errores