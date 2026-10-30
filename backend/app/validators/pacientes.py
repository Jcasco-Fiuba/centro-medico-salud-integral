def validar_dni(dni):
    valido = True

    if len(dni) < 7 or len(dni) > 8:
        valido = False
    elif not dni.isdigit():
        valido = False

    return valido


def validar_nombre(nombre):
    valido = True

    if len(nombre.strip()) == 0 or len(nombre) > 50:
        valido = False
    else:
        for caracter in nombre:
            if not caracter.isalpha() and caracter != " ":
                valido = False

    return valido


def validar_email(email):
    valido = True

    if len(email) == 0 or len(email) > 100:
        valido = False
    elif email.count("@") != 1:
        valido = False
    elif " " in email:
        valido = False
    else:
        partes = email.split("@")

        if len(partes[0]) == 0:
            valido = False
        elif len(partes[1]) == 0:
            valido = False
        elif "." not in partes[1]:
            valido = False
        elif partes[1][0] == "." or partes[1][-1] == ".":
            valido = False
        elif ".." in email:
            valido = False

    return valido


def validar_registro_paciente(datos):
    errores = []

    campos = ["dni", "nombre", "apellido", "email"]

    for campo in campos:
        if campo not in datos:
            errores.append("Falta el campo " + campo)
        elif type(datos[campo]) != str:
            errores.append("El campo " + campo + " debe ser texto")

    if len(errores) == 0:
        if not validar_dni(datos["dni"]):
            errores.append("El DNI no es valido")

        if not validar_nombre(datos["nombre"]):
            errores.append("El nombre no es valido")

        if not validar_nombre(datos["apellido"]):
            errores.append("El apellido no es valido")

        if not validar_email(datos["email"]):
            errores.append("El email no es valido")

    return errores

    
def validar_actualizacion_paciente(datos):
    errores = []

    campos = ["nombre", "apellido", "email"]

    if len(datos) == 0:
        errores.append("No se enviaron datos para actualizar")

    for campo in datos:
        if campo not in campos:
            errores.append("El campo " + campo + " no se puede modificar")
        elif type(datos[campo]) != str:
            errores.append("El campo " + campo + " debe ser texto")
        elif campo == "nombre" or campo == "apellido":
            if not validar_nombre(datos[campo]):
                errores.append("El campo " + campo + " no es valido")
        elif campo == "email":
            if not validar_email(datos[campo]):
                errores.append("El email no es valido")

    return errores
