from datetime import datetime,timedelta
import secrets
import io
import qrcode

from app import db

from app.validators.turnos import (
    validar_get_turnos,
    validar_post_turno,
    validar_reserva_turno,
    validar_consulta_disponible,
    validar_checkin
)

def obtener_turno(id):
    turno = db.buscar_turno_id(id)
    return turno

def listar_turnos(medico, estado):
    turnos = buscar_turnos(medico, estado)
    return turnos

def crear_turno(datos):
    id_medico = datos["id_medico"]
    id_consultorio = datos["id_consultorio"]
    fecha_hora = datos["fecha_hora"]

    medico= buscar_medico_id(id_medico)
    if medico is None:
        return None, "El medico no existe"
    if not medico["activo"]:
        return None, "El medico no esta disponible"

    consultorio = buscar_consultorio_id(id_consultorio)
    if consultorio is None:
        return None, "El consultorio no existe"
    if not consultorio["activo"]:
        return None, "El consultorio no esta activo"
    if medico["id_consultorio"] != id_consultorio:
        return None, "El medico no atiende en ese consultorio"

    if buscar_turnos_superpuestos(id_medico, id_consultorio, fecha_hora):
        return None, "Ya existe un turno en ese horario"

    turno = insertar_turno(id_medico, id_consultorio, fecha_hora)

    return turno, None

def _generar_qr_png(dato: str) -> bytes:
    imagen = qrcode.make(dato)
    buffer = io.BytesIO()
    imagen.save(buffer, format='PNG')
    return buffer.getvalue()

def reservar_turno(datos, usuario_id):
    turno_id = datos["turno_id"]
    turno = buscar_turno_id(turno_id)

    if turno is None:
        return None, "El turno no existe"

    if turno["estado"] != "disponible":
        return None, "El turno no esta disponible"

    if turno["fecha_hora"] <= datetime.now():
        return None, "No se puede reservar un turno que ya paso"

    token = secrets.token_urlsafe(32)
    turno_reservado = actualizar_reserva_turno(turno_id, usuario_id, token)

    if turno_reservado is None:
        return None, "El turno no esta disponible"
    qr_png= _generar_qr_png(token)
    return turno_reservado, None

def listar_turnos_disponibles(medico, fecha):
    datos = {}

    if medico is not None:
        datos["medico"] = medico
    if fecha is not None:
        datos["fecha"] = fecha

    errores = validar_consulta_disponible(datos)
    if errores:
        raise ValueError("; ".join(errores))

    turnos = db.buscar_turnos_disponibles(int(medico), fecha)
    return turnos

def listar_sala_espera():
    fecha = datetime.now().date()
    turnos = db.buscar_turnos_sala_espera(fecha)
    return turnos

def atender_turno(id):
    turno = db.buscar_turno_id(id)
    if not turno:
        return None

    if turno["estado"] != "confirmado":
        raise ValueError("El turno no esta confirmado")

    turno_actualizado = db.actualizar_turno_atendido(id)
    if turno_actualizado is None:
        raise ValueError("No se pudo atender el turno")

    return turno_actualizado

def cancelar_turno(id, usuario_id):
    turno = db.buscar_turno_id(id)

    if not turno:
        return None
    if turno["id_usuario"] != usuario_id:
        raise PermissionError("No puedes cancelar un turno de otro paciente")
    if turno["estado"] != "reservado":
        raise ValueError("El turno no esta reservado")

    turno_cancelado = db.actualizar_cancelacion_turno(id, usuario_id)

    if turno_cancelado is None:
        raise ValueError("No se pudo cancelar el turno")

    return turno_cancelado

def realizar_checkin(datos):
    errores = validar_checkin(datos)
    if errores:
        raise ValueError("; ".join(errores))

    token = datos["string_token"]
    turno = db.buscar_turno_por_token(token)

    if turno is None:
        return None
    if turno["estado"] != "reservado":
        raise ValueError("El turno no esta reservado")

    fecha_turno = turno["fecha_hora"]
    ahora = datetime.now()

    if ahora < fecha_turno - timedelta(minutes=15):
        raise ValueError("Todavia es temprano para hacer el check-in")

    if ahora > fecha_turno + timedelta(minutes=15):
        turno_ausente = db.marcar_turno_ausente(turno["id"])
        if turno_ausente is None:
            raise ValueError("No se pudo registrar la ausencia")
        return turno_ausente

    turno_confirmado = db.registrar_checkin(turno["id"], ahora)
    if turno_confirmado is None:
        raise ValueError("No se pudo registrar el check-in")

    return turno_confirmado