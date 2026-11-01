from datetime import datetime
import secrets
import io
import qrcode

def obtener_turno(id):
    turno = buscar_turno_id(id)
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

