"""Servicios de negocio para el módulo de turnos."""

import base64
from datetime import datetime, timedelta
import io
import secrets

import qrcode

from app.repository import consultorios as repo_consultorios
from app.repository import medicos as repo_medicos
from app.repository import turnos as repo_turno
from app.validators.turnos import (
    validar_checkin,
    validar_consulta_disponible,
    validar_get_turnos,
    validar_id_turno,
    validar_post_turno,
    validar_reserva_turno,
)


def _parsear_fecha_hora(valor: str | datetime) -> datetime:
    if isinstance(valor, datetime):
        return valor
    formatos = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    )
    for fmt in formatos:
        try:
            return datetime.strptime(valor, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(valor)


def _generar_qr_base64(dato: str) -> str:
    imagen = qrcode.make(dato)
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _sin_token(turno: dict | None) -> dict | None:
    if turno is None:
        return None
    return {clave: valor for clave, valor in turno.items() if clave != "string_token"}


def obtener_turno(id_turno: int) -> dict | None:
    if not validar_id_turno(id_turno):
        raise ValueError("El ID del turno debe ser un entero positivo")
    turno = repo_turno.buscar_turno_id(int(id_turno))
    return _sin_token(turno)


def listar_turnos(medico=None, estado=None, dni=None) -> list[dict]:
    datos = {}
    if medico is not None:
        datos["medico"] = medico
    if estado is not None:
        datos["estado"] = estado
    if dni is not None:
        datos["dni"] = dni

    errores = validar_get_turnos(datos)
    if errores:
        raise ValueError("; ".join(errores))

    if dni is not None:
        turnos = repo_turno.buscar_turno_dni(str(dni))
        if medico is not None:
            turnos = [t for t in turnos if t.get("id_medico") == int(medico)]
        if estado is not None:
            turnos = [t for t in turnos if t.get("estado") == estado]
        return [_sin_token(t) for t in turnos if t is not None]

    turnos = repo_turno.listar_turnos(
        medico=int(medico) if medico is not None else None,
        estado=estado,
    )
    return [_sin_token(t) for t in turnos if t is not None]


def crear_turno(datos: dict):
    errores = validar_post_turno(datos)
    if errores:
        return None, "; ".join(errores)

    id_medico = datos["id_medico"]
    id_consultorio = datos["id_consultorio"]
    fecha = _parsear_fecha_hora(datos["fecha_hora"])

    if fecha < datetime.now():
        return None, "No se puede crear un turno en el pasado"

    medico = repo_medicos.obtener_medico_por_id(id_medico)
    if not medico:
        return None, "El medico no existe"
    if not medico.get("activo"):
        return None, "El medico no esta disponible"

    consultorio = repo_consultorios.obtener_por_id(id_consultorio)
    if not consultorio:
        return None, "El consultorio no existe"
    if not consultorio.get("activo"):
        return None, "El consultorio no esta activo"
    if medico.get("id_consultorio") != id_consultorio:
        return None, "El medico no atiende en ese consultorio"

    if repo_turno.verificar_turnos_superpuestos(id_medico, id_consultorio, fecha):
        return None, "Ya existe un turno en ese horario"

    turno = repo_turno.crear_turno(
        {
            "id_medico": id_medico,
            "id_consultorio": id_consultorio,
            "fecha_hora": fecha,
        }
    )
    if not turno:
        return None, "No se pudo crear el turno"

    return _sin_token(turno), None


def reservar_turno(datos: dict, usuario_id: int):
    errores = validar_reserva_turno(datos)
    if errores:
        return None, "; ".join(errores)

    turno_id = datos["turno_id"]
    turno = repo_turno.buscar_turno_id(turno_id)

    if not turno:
        return None, "El turno no existe"
    if turno.get("estado") != "disponible":
        return None, "El turno no esta disponible"

    fecha_hora = _parsear_fecha_hora(turno["fecha_hora"])
    if fecha_hora <= datetime.now():
        return None, "No se puede reservar un turno que ya paso"

    token = secrets.token_urlsafe(32)
    turno_reservado = repo_turno.actualizar_reserva_turno(turno_id, usuario_id, token)
    if turno_reservado is None:
        return None, "El turno no esta disponible"

    qr_b64 = _generar_qr_base64(token)
    resultado = {
        **_sin_token(turno_reservado),
        "qr_token": token,
        "qr_base64": qr_b64,
        "qr_data_url": f"data:image/png;base64,{qr_b64}",
    }
    return resultado, None


def listar_turnos_disponibles(medico, fecha) -> list[dict]:
    datos = {}
    if medico is not None:
        datos["medico"] = medico
    if fecha is not None:
        datos["fecha"] = fecha

    errores = validar_consulta_disponible(datos)
    if errores:
        raise ValueError("; ".join(errores))

    return repo_turno.buscar_turnos_disponibles(int(medico), str(fecha))


def listar_sala_espera() -> list[dict]:
    fecha_hoy = datetime.now().date().isoformat()
    return repo_turno.buscar_turnos_sala_espera(fecha_hoy)


def atender_turno(id_turno: int) -> dict | None:
    turno = repo_turno.buscar_turno_id(id_turno)
    if not turno:
        return None
    if turno.get("estado") != "confirmado":
        raise ValueError("El turno no esta confirmado")

    turno_actualizado = repo_turno.actualizar_turno_atendido(id_turno)
    if turno_actualizado is None:
        raise ValueError("No se pudo atender el turno")

    return _sin_token(turno_actualizado)


def cancelar_turno(id_turno: int, usuario_id: int | None = None) -> dict | None:
    turno = repo_turno.buscar_turno_id(id_turno)
    if not turno:
        return None
    if usuario_id is not None and turno.get("id_usuario") != int(usuario_id):
        raise PermissionError("No puedes cancelar un turno de otro paciente")
    if turno.get("estado") != "reservado":
        raise ValueError("El turno no esta reservado")

    turno_cancelado = repo_turno.actualizar_cancelacion_turno(id_turno, usuario_id)
    if turno_cancelado is None:
        raise ValueError("No se pudo cancelar el turno")

    return _sin_token(turno_cancelado)


def realizar_checkin(datos: dict) -> dict | None:
    errores = validar_checkin(datos)
    if errores:
        raise ValueError("; ".join(errores))

    token = datos["string_token"].strip()
    turno = repo_turno.buscar_turno_por_token(token)
    if turno is None:
        return None
    if turno.get("estado") != "reservado":
        raise ValueError("El turno no esta reservado")

    fecha_turno = _parsear_fecha_hora(turno["fecha_hora"])
    ahora = datetime.now()

    if ahora < fecha_turno - timedelta(minutes=15):
        raise ValueError("Todavia es temprano para hacer el check-in")

    if ahora > fecha_turno + timedelta(minutes=15):
        turno_ausente = repo_turno.marcar_turno_ausente(turno["id"])
        if turno_ausente is None:
            raise ValueError("No se pudo registrar la ausencia")
        return _sin_token(turno_ausente)

    turno_confirmado = repo_turno.registrar_checkin(turno["id"], ahora)
    if turno_confirmado is None:
        raise ValueError("No se pudo registrar el check-in")

    return _sin_token(turno_confirmado)
