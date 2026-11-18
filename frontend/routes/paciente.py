"""Rutas del portal autenticado de pacientes."""

import calendar
from datetime import date, datetime, timedelta
import html
from urllib.parse import urlencode

from flask import (
    Blueprint,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services import api_client

paciente_bp = Blueprint("paciente", __name__, url_prefix="/paciente")

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGOS = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
DURACION_TURNO = 30
ESTADOS_TURNO = ("reservado", "confirmado", "atendido", "cancelado", "ausente")
SEDE_NOMBRE = "Sede Central"


@paciente_bp.before_request
def exigir_sesion_paciente():
    """Exige una sesión autenticada válida antes de entrar a cualquier ruta de `/paciente`."""
    if not api_client.sesion_paciente_activa():
        api_client.cerrar_sesion_autenticada()
        if request.endpoint == "paciente.confirmar_reserva" and request.method == "POST":
            params = {
                clave: request.form.get(clave, "").strip()
                for clave in ("especialidad", "medico", "fecha", "turno")
                if request.form.get(clave, "").strip()
            }
            destino = url_for("paciente.confirmar_reserva", **params)
        else:
            destino = api_client.construir_destino_actual(request, url_for("paciente.portal"))
        return redirect(url_for("auth.iniciar_sesion", next=destino))

    usuario = api_client.obtener_usuario_actual()
    if usuario is not None and usuario.get("rol") not in (None, "paciente", "admin"):
        return ("No tiene permisos para acceder al portal de pacientes.", 403)
    return None


def _iniciales(nombre: str, apellido: str) -> str:
    iniciales = f"{nombre[:1]}{apellido[:1]}".strip().upper()
    return iniciales or "P"


def _hoy_texto(ahora: datetime) -> str:
    return f"{DIAS[ahora.weekday()]} {ahora.day} {MESES[ahora.month - 1]} {ahora.year}"


def _extraer_error_api(respuesta, fallback: str) -> str:
    if isinstance(respuesta, dict):
        errores = respuesta.get("errores")
        if isinstance(errores, list) and errores:
            return str(errores[0])
        error = respuesta.get("error")
        if isinstance(error, str) and error.strip():
            return error.strip()
    return fallback


def _parsear_fecha_api(valor) -> datetime | None:
    if isinstance(valor, datetime):
        return valor
    if not isinstance(valor, str) or not valor.strip():
        return None
    formatos = (
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    )
    texto = valor.strip()
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    return None


def _cargar_paciente_sesion():
    """Carga el perfil del paciente autenticado vía JWT sin fallbacks fijos."""
    usuario = api_client.obtener_usuario_actual() or {}
    dni = str(usuario.get("dni", "")).strip()
    base_usuario = {
        "id": usuario.get("id_usuario") or usuario.get("id"),
        "dni": dni,
        "nombre": str(usuario.get("nombre", "")).strip() or "Paciente",
        "apellido": str(usuario.get("apellido", "")).strip(),
        "email": str(usuario.get("email", "")).strip(),
    }
    base_usuario["iniciales"] = _iniciales(base_usuario["nombre"], base_usuario["apellido"])

    if not dni:
        return base_usuario, "No pudimos identificar el DNI de tu sesión."

    respuesta, status = api_client.get(f"/api/pacientes/{dni}")
    if status == 200 and isinstance(respuesta, dict) and isinstance(respuesta.get("paciente"), dict):
        paciente = dict(respuesta["paciente"])
        paciente["iniciales"] = _iniciales(
            str(paciente.get("nombre", "")), str(paciente.get("apellido", ""))
        )
        return paciente, None

    return base_usuario, _extraer_error_api(respuesta, "No encontramos tus datos de paciente.")


def _obtener_medico_y_consultorio(id_medico: int | None, cache_medicos=None, cache_consultorios=None):
    """Resuelve detalle de médico (con especialidades) y su consultorio desde la API."""
    if not id_medico:
        return None, None
    cache_medicos = cache_medicos if cache_medicos is not None else {}
    cache_consultorios = cache_consultorios if cache_consultorios is not None else {}

    if id_medico not in cache_medicos:
        resp, status = api_client.get(f"/api/medicos/{id_medico}")
        cache_medicos[id_medico] = resp if status == 200 and isinstance(resp, dict) else None
    medico = cache_medicos[id_medico]

    consultorio = None
    id_consultorio = medico.get("id_consultorio") if isinstance(medico, dict) else None
    if id_consultorio:
        if id_consultorio not in cache_consultorios:
            resp_c, status_c = api_client.get(f"/api/consultorios/{id_consultorio}")
            if status_c == 200 and isinstance(resp_c, dict):
                cache_consultorios[id_consultorio] = resp_c.get("consultorio")
            else:
                cache_consultorios[id_consultorio] = None
        consultorio = cache_consultorios[id_consultorio]

    return medico, consultorio


def _obtener_especialidad_por_id(especialidad_id: int | None):
    if not especialidad_id:
        return None
    resp, status = api_client.get(f"/api/especialidades/{especialidad_id}")
    if status == 200 and isinstance(resp, dict) and "id" in resp:
        return resp
    return None


def _buscar_turnos_disponibles_dia(medico_id: int, fecha_iso: str) -> tuple[list[dict], bool]:
    """Consulta disponibilidad de un día; devuelve `(slots, conexion_ok)`."""
    ruta = "/api/turnos/disponibles?" + urlencode({"medico": medico_id, "fecha": fecha_iso})
    resp, status = api_client.get(ruta)
    if status == 200 and isinstance(resp, list):
        return resp, True
    if status >= 500 or status == 401:
        return [], False
    return [], True


def _proximo_turno_disponible_medico(medico_id: int, ahora: datetime, dias_horizonte: int = 14) -> datetime | None:
    """Busca el próximo turno disponible real vía `GET /api/turnos/disponibles`."""
    for offset in range(dias_horizonte + 1):
        fecha_dia = (ahora.date() + timedelta(days=offset)).isoformat()
        slots, ok = _buscar_turnos_disponibles_dia(medico_id, fecha_dia)
        if not ok:
            return None
        futuros = []
        for slot in slots:
            dt = _parsear_fecha_api(slot.get("fecha_hora"))
            if dt is not None and dt >= ahora:
                futuros.append(dt)
        if futuros:
            return min(futuros)
    return None


def _formatear_consultorio(consultorio: dict | None, turno: dict | None = None) -> tuple[str, str]:
    if isinstance(consultorio, dict):
        nombre = str(consultorio.get("nombre", "")).strip()
        ubicacion = str(consultorio.get("ubicacion", "")).strip()
        if nombre and ubicacion:
            return f"{nombre} · {ubicacion}", nombre
        if nombre:
            return nombre, nombre
    if isinstance(turno, dict) and turno.get("consultorio"):
        nombre = str(turno.get("consultorio", "")).strip()
        ubicacion = str(turno.get("ubicacion", "")).strip()
        return (f"{nombre} · {ubicacion}" if ubicacion else nombre), nombre
    return SEDE_NOMBRE, SEDE_NOMBRE


def _construir_vista_turno(turno_raw: dict, medico: dict | None, consultorio: dict | None, ahora: datetime) -> dict:
    """Normaliza los campos comunes usados por las plantillas de turnos del paciente."""
    fecha_dt = _parsear_fecha_api(turno_raw.get("fecha_hora")) or ahora
    checkin_dt = _parsear_fecha_api(turno_raw.get("hora_checkin"))

    especialidades_medico = medico.get("especialidades", []) if isinstance(medico, dict) else []
    nombres_esp = [e.get("nombre", "") for e in especialidades_medico if e.get("nombre")]
    ids_esp = [e.get("id") for e in especialidades_medico if e.get("id") is not None]
    especialidad_texto = ", ".join(nombres_esp) if nombres_esp else "Consulta médica"

    if isinstance(medico, dict):
        medico_texto = f"{medico.get('nombre', '')} {medico.get('apellido', '')}".strip()
    elif turno_raw.get("medico_nombre") or turno_raw.get("medico_apellido"):
        medico_texto = f"{turno_raw.get('medico_nombre', '')} {turno_raw.get('medico_apellido', '')}".strip()
    else:
        medico_texto = f"Médico #{turno_raw.get('id_medico', '')}"

    consultorio_texto, consultorio_nombre = _formatear_consultorio(consultorio, turno_raw)

    desde = fecha_dt - timedelta(minutes=15)
    hasta = fecha_dt + timedelta(minutes=15)
    limite_cancelar = fecha_dt - timedelta(hours=24)
    estado = str(turno_raw.get("estado", "")).lower()
    puede_cancelar = estado == "reservado" and ahora <= limite_cancelar
    es_proximo = estado in ("reservado", "confirmado") and fecha_dt >= ahora

    qr_turnos = session.get("qr_turnos", {})
    qr_url = qr_turnos.get(str(turno_raw.get("id"))) if isinstance(qr_turnos, dict) else None

    return {
        "id": turno_raw["id"],
        "id_medico": turno_raw.get("id_medico"),
        "id_consultorio": turno_raw.get("id_consultorio"),
        "codigo": f"Turno N.º {turno_raw['id']}",
        "estado": estado,
        "especialidad": especialidad_texto,
        "especialidades_ids": ids_esp,
        "medico": medico_texto,
        "dia": f"{fecha_dt.day:02d}",
        "mes": MESES[fecha_dt.month - 1].upper(),
        "fecha": f"{DIAS[fecha_dt.weekday()]} {fecha_dt.strftime('%d/%m/%Y')}",
        "fecha_dmy": fecha_dt.strftime("%d/%m/%Y"),
        "fecha_numerica": fecha_dt.strftime("%d/%m/%Y"),
        "fecha_completa": f"{DIAS[fecha_dt.weekday()]} {fecha_dt.day} de {MESES_LARGOS[fecha_dt.month - 1]} de {fecha_dt.year}",
        "fecha_corta": fecha_dt.strftime("%d/%m"),
        "hora": fecha_dt.strftime("%H:%M"),
        "duracion": DURACION_TURNO,
        "consultorio": consultorio_texto,
        "consultorio_nombre": consultorio_nombre,
        "sede": SEDE_NOMBRE,
        "qr_url": qr_url,
        "emitido": None,
        "checkin_desde": desde.strftime("%H:%M"),
        "checkin_hasta": hasta.strftime("%H:%M"),
        "limite_ausente": hasta.strftime("%H:%M"),
        "checkin_hora": checkin_dt.strftime("%H:%M") if checkin_dt else None,
        "cancelado_el": None,
        "puede_cancelar": puede_cancelar,
        "es_proximo": es_proximo,
        "cancelar_hasta": limite_cancelar.strftime("%d/%m a las %H:%M h"),
        "texto_checkin": (
            f"El {fecha_dt.strftime('%d/%m')} podés registrar tu llegada entre las "
            f"{desde.strftime('%H:%M')} y las {hasta.strftime('%H:%M')} h inclusive."
        ),
        "_fecha_dt": fecha_dt,
    }


def _armar_calendario_mes(anio: int, mes: int, medico_id: int, fecha_sel: date | None, hoy: date) -> tuple[list, dict]:
    """Construye la matriz semanal del calendario y consulta días con turnos disponibles."""
    cal = calendar.Calendar(firstweekday=0)
    dias_mes = cal.monthdatescalendar(anio, mes)
    dias_disponibles: set[str] = set()
    slots_por_dia: dict[str, list[dict]] = {}

    conexion_ok = True
    for semana in dias_mes:
        for d in semana:
            if d.month == mes and d >= hoy and conexion_ok:
                iso = d.isoformat()
                slots, conexion_ok = _buscar_turnos_disponibles_dia(medico_id, iso)
                if slots:
                    dias_disponibles.add(iso)
                    slots_por_dia[iso] = slots

    semanas = []
    for semana in dias_mes:
        fila = []
        for d in semana:
            if d.month != mes:
                fila.append(None)
            else:
                iso = d.isoformat()
                fila.append(
                    {
                        "dia": d.day,
                        "iso": iso,
                        "pasado": d < hoy,
                        "disponible": iso in dias_disponibles,
                        "seleccionado": fecha_sel == d,
                    }
                )
        semanas.append(fila)
    return semanas, slots_por_dia


@paciente_bp.route("/")
def portal():
    """Portal del paciente autenticado: perfil y próximo turno."""
    ahora = datetime.now()
    hoy = _hoy_texto(ahora)
    paciente, error_paciente = _cargar_paciente_sesion()

    resp_turnos, status_turnos = api_client.get("/api/turnos")
    if status_turnos != 200 or not isinstance(resp_turnos, list):
        return render_template(
            "paciente/portal.html",
            hoy=hoy,
            paciente=paciente,
            proximo_turno=None,
            error=error_paciente or _extraer_error_api(resp_turnos, "No se pudieron cargar tus turnos."),
        )

    turno_elegido = None
    fecha_elegida = None
    for turno in resp_turnos:
        fecha_dt = _parsear_fecha_api(turno.get("fecha_hora"))
        estado = str(turno.get("estado", "")).lower()
        if fecha_dt is not None and estado in ("reservado", "confirmado") and fecha_dt >= ahora:
            if fecha_elegida is None or fecha_dt < fecha_elegida:
                turno_elegido = turno
                fecha_elegida = fecha_dt

    proximo_turno = None
    if turno_elegido is not None:
        medico, consultorio = _obtener_medico_y_consultorio(turno_elegido.get("id_medico"))
        proximo_turno = _construir_vista_turno(turno_elegido, medico, consultorio, ahora)

    return render_template(
        "paciente/portal.html",
        hoy=hoy,
        paciente=paciente,
        proximo_turno=proximo_turno,
        error=error_paciente,
    )


@paciente_bp.route("/reservar/especialidad")
def elegir_especialidad():
    """Paso 1 de la reserva: muestra las especialidades activas."""
    busqueda = request.args.get("busqueda", "")
    especialidad_id = request.args.get("especialidad", type=int)
    paciente, error_paciente = _cargar_paciente_sesion()

    respuesta, status = api_client.get("/api/especialidades")
    if status != 200 or not isinstance(respuesta, dict):
        return render_template(
            "paciente/especialidad.html",
            paciente=paciente,
            especialidades=[],
            busqueda=busqueda,
            especialidad=None,
            error=error_paciente or _extraer_error_api(respuesta, "No pudimos cargar las especialidades."),
        )

    especialidades = []
    especialidad = None
    for item in respuesta.get("especialidades", []):
        if item.get("activo") is False:
            continue
        if busqueda.strip().lower() in str(item.get("nombre", "")).lower():
            especialidades.append(item)
        if item.get("id") == especialidad_id:
            especialidad = item

    return render_template(
        "paciente/especialidad.html",
        paciente=paciente,
        especialidades=especialidades,
        busqueda=busqueda,
        especialidad=especialidad,
        error=error_paciente,
    )


@paciente_bp.route("/reservar/profesional")
def elegir_profesional():
    """Paso 2 de la reserva: médicos activos de la especialidad elegida."""
    especialidad_id = request.args.get("especialidad", type=int)
    medico_id = request.args.get("medico", type=int)
    busqueda = request.args.get("busqueda", "")

    if especialidad_id is None or especialidad_id <= 0:
        return redirect(url_for("paciente.elegir_especialidad"))

    paciente, error_paciente = _cargar_paciente_sesion()
    especialidad = _obtener_especialidad_por_id(especialidad_id) or {
        "id": especialidad_id,
        "nombre": "Especialidad seleccionada",
    }

    respuesta, status = api_client.get(f"/api/medicos?especialidad={especialidad_id}")
    if status != 200 or not isinstance(respuesta, list):
        return render_template(
            "paciente/profesional.html",
            paciente=paciente,
            medicos=[],
            busqueda=busqueda,
            especialidad_id=especialidad_id,
            especialidad=especialidad,
            medico=None,
            error=error_paciente or _extraer_error_api(respuesta, "No se pudieron cargar los profesionales."),
        )

    ahora = datetime.now()
    medicos = []
    medico_elegido = None
    for item in respuesta:
        if not item.get("activo"):
            continue
        nombre_completo = f"{item.get('nombre', '')} {item.get('apellido', '')}".strip()
        if busqueda.strip().lower() not in nombre_completo.lower():
            continue

        proxima_fecha = _proximo_turno_disponible_medico(item["id"], ahora)
        medico_vista = dict(item)
        medico_vista["nombre_completo"] = nombre_completo
        medico_vista["iniciales"] = _iniciales(str(item.get("nombre", "")), str(item.get("apellido", "")))
        medico_vista["proximo"] = (
            f"{DIAS[proxima_fecha.weekday()][:3]} {proxima_fecha.day} "
            f"{MESES[proxima_fecha.month - 1]} · desde las {proxima_fecha.strftime('%H:%M')} h"
            if proxima_fecha is not None
            else None
        )
        medicos.append(medico_vista)
        if item.get("id") == medico_id:
            medico_elegido = medico_vista

    return render_template(
        "paciente/profesional.html",
        paciente=paciente,
        medicos=medicos,
        busqueda=busqueda,
        especialidad_id=especialidad_id,
        especialidad=especialidad,
        medico=medico_elegido,
        error=error_paciente,
    )


@paciente_bp.route("/reservar/fecha")
def elegir_fecha():
    """Paso 3 de la reserva: calendario mensual y horarios disponibles del día."""
    especialidad_id = request.args.get("especialidad", type=int)
    medico_id = request.args.get("medico", type=int)

    if not especialidad_id or especialidad_id <= 0:
        return redirect(url_for("paciente.elegir_especialidad"))
    if not medico_id or medico_id <= 0:
        return redirect(url_for("paciente.elegir_profesional", especialidad=especialidad_id))

    paciente, error_paciente = _cargar_paciente_sesion()
    especialidad = _obtener_especialidad_por_id(especialidad_id) or {
        "id": especialidad_id,
        "nombre": "Especialidad",
    }
    medico_raw, consultorio_raw = _obtener_medico_y_consultorio(medico_id)
    if medico_raw is None:
        return redirect(url_for("paciente.elegir_profesional", especialidad=especialidad_id))

    medico = {
        **medico_raw,
        "nombre_completo": f"{medico_raw.get('nombre', '')} {medico_raw.get('apellido', '')}".strip(),
    }
    consultorio_texto, _ = _formatear_consultorio(consultorio_raw)

    ahora = datetime.now()
    hoy = ahora.date()

    mes_param = request.args.get("mes", "").strip()
    anio, mes_num = hoy.year, hoy.month
    if mes_param:
        try:
            anio_str, mes_str = mes_param.split("-")
            anio_cand, mes_cand = int(anio_str), int(mes_str)
            if 1 <= mes_cand <= 12 and (anio_cand, mes_cand) >= (hoy.year, hoy.month):
                anio, mes_num = anio_cand, mes_cand
        except ValueError:
            pass

    mes_actual = f"{anio:04d}-{mes_num:02d}"
    mes_titulo = f"{MESES_LARGOS[mes_num - 1].capitalize()} {anio}"
    if (anio, mes_num) > (hoy.year, hoy.month):
        prev_anio, prev_mes = (anio - 1, 12) if mes_num == 1 else (anio, mes_num - 1)
        mes_anterior = f"{prev_anio:04d}-{prev_mes:02d}"
    else:
        mes_anterior = None
    sig_anio, sig_mes = (anio + 1, 1) if mes_num == 12 else (anio, mes_num + 1)
    mes_siguiente = f"{sig_anio:04d}-{sig_mes:02d}"

    fecha_param = request.args.get("fecha", "").strip()
    fecha_sel = None
    fecha_info = None
    fecha_pasada = False
    if fecha_param:
        try:
            fecha_sel = date.fromisoformat(fecha_param)
            fecha_pasada = fecha_sel < hoy
            fecha_info = {
                "iso": fecha_sel.isoformat(),
                "titulo": f"{DIAS[fecha_sel.weekday()]} {fecha_sel.day} de {MESES_LARGOS[fecha_sel.month - 1]}",
                "subtitulo": f"Horarios de {DURACION_TURNO} minutos disponibles para {medico['nombre_completo']}.",
                "corta": fecha_sel.strftime("%d/%m/%Y"),
            }
        except ValueError:
            fecha_sel = None

    semanas, slots_por_dia = _armar_calendario_mes(anio, mes_num, medico_id, fecha_sel, hoy)

    horarios = []
    if fecha_sel is not None and not fecha_pasada:
        slots = slots_por_dia.get(fecha_sel.isoformat())
        if slots is None:
            slots, _ = _buscar_turnos_disponibles_dia(medico_id, fecha_sel.isoformat())
        for slot in slots:
            dt = _parsear_fecha_api(slot.get("fecha_hora"))
            if dt is not None and dt >= ahora:
                horarios.append({"id": slot["id"], "hora": dt.strftime("%H:%M")})

    return render_template(
        "paciente/elegir_fecha.html",
        paciente=paciente,
        especialidad_id=especialidad_id,
        especialidad=especialidad,
        medico_id=medico_id,
        medico=medico,
        consultorio=consultorio_texto,
        error=error_paciente,
        mes=mes_actual,
        mes_titulo=mes_titulo,
        mes_anterior=mes_anterior,
        mes_siguiente=mes_siguiente,
        semanas=semanas,
        hoy_texto=_hoy_texto(ahora),
        fecha=fecha_info,
        fecha_pasada=fecha_pasada,
        horarios=horarios,
    )


@paciente_bp.route("/reservar/confirmar", methods=["GET", "POST"])
def confirmar_reserva():
    """Paso 4 de la reserva: revisión y confirmación vía `POST /api/turnos/reservar`."""
    especialidad_id = request.values.get("especialidad", type=int) or 0
    turno_id = request.values.get("turno", type=int)
    medico_id = request.values.get("medico", type=int)
    fecha_iso = request.values.get("fecha", "").strip()

    if not turno_id or turno_id <= 0:
        return redirect(url_for("paciente.elegir_especialidad"))

    ahora = datetime.now()
    paciente, _ = _cargar_paciente_sesion()
    especialidad = _obtener_especialidad_por_id(especialidad_id)
    especialidad_nombre = (
        especialidad["nombre"] if isinstance(especialidad, dict) else "Consulta médica"
    )

    slot_encontrado = None
    problema = None

    # 1. Revisar si ya figura entre las reservas del propio paciente
    mis_turnos, status_mios = api_client.get("/api/turnos")
    if status_mios == 200 and isinstance(mis_turnos, list):
        for t in mis_turnos:
            if t.get("id") == turno_id and str(t.get("estado", "")).lower() in ("reservado", "confirmado"):
                slot_encontrado = t
                problema = "duplicado"
                break

    # 2. Si viene del paso 3 con medico + fecha, buscar en disponibilidad pública
    if slot_encontrado is None and medico_id and fecha_iso:
        slots, _ = _buscar_turnos_disponibles_dia(medico_id, fecha_iso)
        for slot in slots:
            if slot.get("id") == turno_id:
                slot_encontrado = slot
                break

    # 3. Fallback si fue ocupado justo antes o llegó sin medico/fecha
    if slot_encontrado is None:
        resp_detalle, status_detalle = api_client.get(f"/api/turnos/{turno_id}")
        if status_detalle == 200 and isinstance(resp_detalle, dict):
            slot_encontrado = resp_detalle
            if str(resp_detalle.get("estado", "")).lower() != "disponible":
                problema = "ocupado"
        else:
            problema = "ocupado"
            slot_encontrado = {
                "id": turno_id,
                "id_medico": medico_id or 0,
                "id_consultorio": None,
                "fecha_hora": f"{fecha_iso} 00:00:00" if fecha_iso else ahora.strftime("%Y-%m-%d %H:%M:%S"),
                "estado": "ocupado",
            }

    if request.method == "POST" and problema is None:
        resp_reserva, status_reserva = api_client.post("/api/turnos/reservar", {"turno_id": turno_id})
        if status_reserva == 200 and isinstance(resp_reserva, dict):
            qr_data_url = resp_reserva.get("qr_data_url")
            if isinstance(qr_data_url, str) and qr_data_url:
                qr_turnos = session.get("qr_turnos")
                if not isinstance(qr_turnos, dict):
                    qr_turnos = {}
                qr_turnos[str(turno_id)] = qr_data_url
                session["qr_turnos"] = qr_turnos
                session.modified = True
            return redirect(url_for("paciente.detalle_turno", turno_id=turno_id, reservado="1"))

        msg_err = _extraer_error_api(resp_reserva, "No se pudo confirmar el turno.")
        if "no esta disponible" in msg_err.lower():
            problema = "ocupado"
        else:
            problema = "error"

    medico_raw, consultorio_raw = _obtener_medico_y_consultorio(slot_encontrado.get("id_medico") or medico_id)
    turno_vista = _construir_vista_turno(slot_encontrado, medico_raw, consultorio_raw, ahora)

    return render_template(
        "paciente/confirmar_reserva.html",
        paciente=paciente,
        especialidad_id=especialidad_id,
        especialidad_nombre=especialidad_nombre,
        medico_id=medico_id or turno_vista.get("id_medico"),
        fecha_iso=fecha_iso,
        turno=turno_vista,
        problema=problema,
    )


@paciente_bp.route("/mis-turnos")
def mis_turnos():
    """Historial y próximos turnos del paciente autenticado con filtros."""
    ahora = datetime.now()
    filtro_estado = request.args.get("estado", "").strip().lower()
    filtro_especialidad = request.args.get("especialidad", type=int)

    paciente, error_paciente = _cargar_paciente_sesion()
    resp_esp, status_esp = api_client.get("/api/especialidades")
    especialidades = (
        resp_esp.get("especialidades", [])
        if status_esp == 200 and isinstance(resp_esp, dict)
        else []
    )

    resp_turnos, status_turnos = api_client.get("/api/turnos")
    if status_turnos != 200 or not isinstance(resp_turnos, list):
        return render_template(
            "paciente/mis_turnos.html",
            paciente=paciente,
            total=0,
            proximos=[],
            anteriores=[],
            estados=ESTADOS_TURNO,
            especialidades=especialidades,
            filtro_estado=filtro_estado,
            filtro_especialidad=filtro_especialidad,
            error=error_paciente or _extraer_error_api(resp_turnos, "No se pudieron cargar tus turnos."),
        )

    cache_medicos = {}
    cache_consultorios = {}
    turnos_vistos = []
    for item in resp_turnos:
        medico, consultorio = _obtener_medico_y_consultorio(
            item.get("id_medico"), cache_medicos, cache_consultorios
        )
        turnos_vistos.append(_construir_vista_turno(item, medico, consultorio, ahora))

    total = len(turnos_vistos)
    filtrados = turnos_vistos
    if filtro_estado:
        filtrados = [t for t in filtrados if t["estado"] == filtro_estado]
    if filtro_especialidad:
        filtrados = [t for t in filtrados if filtro_especialidad in t["especialidades_ids"]]

    proximos = sorted(
        [t for t in filtrados if t["es_proximo"]],
        key=lambda t: t["_fecha_dt"],
    )
    anteriores = sorted(
        [t for t in filtrados if not t["es_proximo"]],
        key=lambda t: t["_fecha_dt"],
        reverse=True,
    )

    return render_template(
        "paciente/mis_turnos.html",
        paciente=paciente,
        total=total,
        proximos=proximos,
        anteriores=anteriores,
        estados=ESTADOS_TURNO,
        especialidades=especialidades,
        filtro_estado=filtro_estado,
        filtro_especialidad=filtro_especialidad,
        error=request.args.get("error") or error_paciente,
    )


@paciente_bp.route("/turnos/<int:turno_id>")
def detalle_turno(turno_id: int):
    """Detalle y comprobante QR del turno del paciente autenticado."""
    ahora = datetime.now()
    paciente, error_paciente = _cargar_paciente_sesion()

    resp_turno, status_turno = api_client.get(f"/api/turnos/{turno_id}")
    if status_turno != 200 or not isinstance(resp_turno, dict):
        return redirect(
            url_for(
                "paciente.mis_turnos",
                error=_extraer_error_api(resp_turno, "No se encontró el turno solicitado."),
            )
        )

    medico, consultorio = _obtener_medico_y_consultorio(resp_turno.get("id_medico"))
    turno_vista = _construir_vista_turno(resp_turno, medico, consultorio, ahora)
    mensaje = (
        "¡Turno confirmado! Presentá tu comprobante en recepción."
        if request.args.get("reservado") == "1"
        else None
    )

    return render_template(
        "paciente/detalle_turno.html",
        hoy=_hoy_texto(ahora),
        paciente=paciente,
        turno=turno_vista,
        error=error_paciente,
        mensaje=mensaje,
    )


@paciente_bp.route("/turnos/<int:turno_id>/cancelar", methods=["GET", "POST"])
def cancelar_turno(turno_id: int):
    """Confirmación y ejecución de cancelación de turno del paciente."""
    ahora = datetime.now()
    hoy = _hoy_texto(ahora)
    paciente, _ = _cargar_paciente_sesion()

    resp_turno, status_turno = api_client.get(f"/api/turnos/{turno_id}")
    if status_turno != 200 or not isinstance(resp_turno, dict):
        return redirect(
            url_for(
                "paciente.mis_turnos",
                error=_extraer_error_api(resp_turno, "No se encontró el turno solicitado."),
            )
        )

    medico, consultorio = _obtener_medico_y_consultorio(resp_turno.get("id_medico"))
    turno_vista = _construir_vista_turno(resp_turno, medico, consultorio, ahora)

    if request.method == "POST":
        if not turno_vista["puede_cancelar"]:
            return render_template(
                "paciente/cancelar_turno.html",
                vista="error",
                hoy=hoy,
                paciente=paciente,
                turno=turno_vista,
            ), 400

        _, status_cancel = api_client.patch(f"/api/turnos/{turno_id}/cancelar")
        if status_cancel == 200:
            qr_turnos = session.get("qr_turnos")
            if isinstance(qr_turnos, dict) and str(turno_id) in qr_turnos:
                qr_turnos.pop(str(turno_id), None)
                session["qr_turnos"] = qr_turnos
                session.modified = True
            return render_template(
                "paciente/cancelar_turno.html",
                vista="exito",
                hoy=hoy,
                cancelado_en=ahora.strftime("%d/%m/%Y a las %H:%M h"),
                paciente=paciente,
                turno=turno_vista,
            )

        return render_template(
            "paciente/cancelar_turno.html",
            vista="error",
            hoy=hoy,
            paciente=paciente,
            turno=turno_vista,
        ), 400

    return render_template(
        "paciente/cancelar_turno.html",
        vista="confirmar",
        hoy=hoy,
        paciente=paciente,
        turno=turno_vista,
    )


@paciente_bp.route("/turnos/<int:turno_id>/comprobante")
def descargar_comprobante(turno_id: int):
    """Genera el comprobante descargable del turno reservado."""
    ahora = datetime.now()
    paciente, _ = _cargar_paciente_sesion()

    resp_turno, status_turno = api_client.get(f"/api/turnos/{turno_id}")
    if status_turno != 200 or not isinstance(resp_turno, dict):
        return redirect(
            url_for(
                "paciente.mis_turnos",
                error=_extraer_error_api(resp_turno, "No se pudo generar el comprobante."),
            )
        )

    medico, consultorio = _obtener_medico_y_consultorio(resp_turno.get("id_medico"))
    turno_vista = _construir_vista_turno(resp_turno, medico, consultorio, ahora)

    qr_bloque = ""
    if turno_vista["qr_url"]:
        qr_bloque = (
            f'<p><img src="{html.escape(turno_vista["qr_url"], quote=True)}" '
            f'alt="QR turno #{turno_id}" style="max-width:220px"></p>'
        )

    documento = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Comprobante {html.escape(turno_vista['codigo'])}</title>
</head>
<body style="font-family:sans-serif;max-width:600px;margin:2rem auto;">
  <h1>Centro Médico Salud Integral</h1>
  <h2>Comprobante de turno — {html.escape(turno_vista['codigo'])}</h2>
  <p><strong>Paciente:</strong> {html.escape(str(paciente['nombre']))} {html.escape(str(paciente['apellido']))} (DNI {html.escape(str(paciente['dni']))})</p>
  <p><strong>Especialidad:</strong> {html.escape(turno_vista['especialidad'])}</p>
  <p><strong>Profesional:</strong> {html.escape(turno_vista['medico'])}</p>
  <p><strong>Fecha y hora:</strong> {html.escape(turno_vista['fecha'])} · {html.escape(turno_vista['hora'])} h ({turno_vista['duracion']} min)</p>
  <p><strong>Consultorio:</strong> {html.escape(turno_vista['consultorio'])}</p>
  <p><strong>Ventana de check-in:</strong> {html.escape(turno_vista['checkin_desde'])} a {html.escape(turno_vista['checkin_hasta'])} h</p>
  {qr_bloque}
</body>
</html>
"""
    return Response(
        documento,
        mimetype="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="comprobante-turno-{turno_id}.html"'
        },
    )
