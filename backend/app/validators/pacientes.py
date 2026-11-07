def validar_dni(dni):

    if len(dni) < 7 or len(dni) > 8:
        raise ValueError("El DNI debe tener entre 7 y 8 digitos")

    if not dni.isdigit():
        raise ValueError("El DNI debe contener solo numeros")


def validar_nombre(nombre):

    if len(nombre.strip()) == 0 or len(nombre) > 100:
        raise ValueError("El nombre debe tener entre 1 y 100 caracteres")

    for caracter in nombre:
        if not caracter.isalpha() and caracter != " ":
            raise ValueError("El nombre solo puede contener letras y espacios")


def validar_email(email):

    if len(email) == 0 or len(email) > 100:
        raise ValueError("El email debe tener entre 1 y 100 caracteres")

    if email.count("@") != 1:
        raise ValueError("El email debe tener una sola arroba")

    if " " in email or ".." in email:
        raise ValueError("El email contiene caracteres no permitidos")

    partes = email.split("@")
    usuario = partes[0]
    dominio = partes[1]

    if len(usuario) == 0 or len(dominio) == 0:
        raise ValueError("El email esta incompleto")

    if "." not in dominio:
        raise ValueError("El dominio debe contener un punto")

    if usuario[0] == "." or usuario[-1] == ".":
        raise ValueError("El usuario del email no es valido")

    if dominio[0] == "." or dominio[-1] == ".":
        raise ValueError("El dominio no es valido")

    partes_dominio = dominio.split(".")

    for parte in partes_dominio:
        if len(parte) == 0:
            raise ValueError("El dominio contiene partes vacias")

    extension = partes_dominio[-1]

    if len(extension) < 2 or not extension.isalpha():
        raise ValueError("La extension del email no es valida")


def validar_password(password):

    if len(password) < 8 or len(password) > 50:
        raise ValueError("La contrasena debe tener entre 8 y 50 caracteres")


def validar_registro_paciente(datos):

    errores = []
    campos = ["dni", "nombre", "apellido", "email", "password"]

    if type(datos) != dict:
        return ["Los datos deben ser un objeto"]

    for campo in campos:
        if campo not in datos:
            errores.append("Falta el campo " + campo)
        elif type(datos[campo]) != str:
            errores.append("El campo " + campo + " debe ser texto")

    for campo in datos:
        if campo not in campos:
            errores.append("El campo " + campo + " no esta permitido")

    if len(errores) == 0:
        for campo in campos:
            try:
                if campo == "dni":
                    validar_dni(datos[campo])
                elif campo == "email":
                    validar_email(datos[campo])
                elif campo == "password":
                    validar_password(datos[campo])
                else:
                    validar_nombre(datos[campo])

            except ValueError as error:
                errores.append("El campo " + campo + ": " + str(error))

    return errores


def validar_actualizacion_paciente(datos):

    errores = []
    campos = ["nombre", "apellido", "email"]

    if type(datos) != dict:
        return ["Los datos deben ser un objeto"]

    if len(datos) == 0:
        errores.append("No se enviaron datos para actualizar")

    for campo in datos:
        if campo not in campos:
            errores.append("El campo " + campo + " no se puede modificar")

        elif type(datos[campo]) != str:
            errores.append("El campo " + campo + " debe ser texto")

        else:
            try:
                if campo == "nombre" or campo == "apellido":
                    validar_nombre(datos[campo])

                elif campo == "email":
                    validar_email(datos[campo])

            except ValueError as error:
                errores.append("El campo " + campo + ": " + str(error))

    return errores


def validar_baja_paciente(dni):

    errores = []

    try:
        validar_dni(dni)
    except ValueError as error:
        errores.append(str(error))

    return errores