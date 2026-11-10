def validar_id_consultorio(id_consultorio):
    texto = str(id_consultorio)

    if not (texto.isascii() and texto.isdigit()):
        return False

    return int(texto) > 0


def validar_texto_consultorio(valor, etiqueta, mensaje_vacio):

    if type(valor) != str:
        return etiqueta + " debe ser texto"

    if len(valor.strip()) == 0:
        return mensaje_vacio

    if len(valor.strip()) > 50:
        return etiqueta + " no puede superar los 50 caracteres"

    return None


def validar_registro_consultorio(datos):
    errores = []

    if not datos:
        errores.append("No se enviaron datos")
        return errores

    if type(datos) != dict:
        errores.append("Los datos deben ser un objeto")
        return errores

    if "nombre" not in datos:
        errores.append("El nombre es obligatorio")
    else:
        error = validar_texto_consultorio(
            datos["nombre"], "El nombre", "El nombre es obligatorio"
        )

        if error:
            errores.append(error)

    if "ubicacion" not in datos:
        errores.append("La ubicacion es obligatoria")
    else:
        error = validar_texto_consultorio(
            datos["ubicacion"], "La ubicacion", "La ubicacion es obligatoria"
        )

        if error:
            errores.append(error)

    return errores


def validar_actualizacion_consultorio(datos):
    errores = []

    if not datos:
        errores.append("No se enviaron datos para actualizar")
        return errores

    if type(datos) != dict:
        errores.append("Los datos deben ser un objeto")
        return errores

    for campo in datos:
        if campo != "nombre" and campo != "ubicacion":
            errores.append("El campo " + campo + " no se puede modificar")

    if "nombre" in datos:
        error = validar_texto_consultorio(
            datos["nombre"], "El nombre", "El nombre no puede estar vacio"
        )

        if error:
            errores.append(error)

    if "ubicacion" in datos:
        error = validar_texto_consultorio(
            datos["ubicacion"], "La ubicacion", "La ubicacion no puede estar vacia"
        )

        if error:
            errores.append(error)

    return errores