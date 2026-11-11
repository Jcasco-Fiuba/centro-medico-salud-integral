def validar_id_especialidad(id_especialidad):
    texto = str(id_especialidad)

    if not (texto.isascii() and texto.isdigit()):
        return False

    return int(texto) > 0


def validar_nombre_especialidad(nombre, mensaje_vacio):
    if type(nombre) != str:
        return "El nombre de la especialidad debe ser texto"

    if len(nombre.strip()) == 0:
        return mensaje_vacio

    if len(nombre.strip()) > 50:
        return "El nombre de la especialidad no puede superar los 50 caracteres"

    return None


def validar_descripcion_especialidad(descripcion):
    if descripcion is None:
        return None

    if type(descripcion) != str:
        return "La descripcion debe ser texto"

    if len(descripcion.strip()) > 255:
        return "La descripcion no puede superar los 255 caracteres"

    return None


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
    else:
        error = validar_nombre_especialidad(
            datos["nombre"], "El nombre de la especialidad es obligatorio"
        )

        if error:
            errores.append(error)

    if "descripcion" in datos:
        error = validar_descripcion_especialidad(datos["descripcion"])

        if error:
            errores.append(error)

    return errores


def validar_actualizacion_especialidad(datos):
    errores = []

    if not datos:
        errores.append("No se enviaron datos para actualizar")
        return errores

    if type(datos) != dict:
        errores.append("Los datos deben ser un objeto")
        return errores

    for campo in datos:
        if campo != "nombre" and campo != "descripcion" and campo != "activo":
            errores.append("El campo " + campo + " no se puede modificar")

    if "nombre" in datos:
        error = validar_nombre_especialidad(
            datos["nombre"], "El nombre de la especialidad no puede estar vacio"
        )

        if error:
            errores.append(error)

    if "descripcion" in datos:
        error = validar_descripcion_especialidad(datos["descripcion"])

        if error:
            errores.append(error)

    if "activo" in datos and type(datos["activo"]) != bool:
        errores.append("El campo activo debe ser true o false")

    return errores
