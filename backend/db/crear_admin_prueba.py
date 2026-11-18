"""Script para crear una cuenta administrativa nueva en MySQL local de desarrollo o prueba.

Medidas de seguridad:
1. Solo inserta cuentas nuevas (`INSERT`). Nunca modifica cuentas existentes ni
   cambia el rol de un paciente o usuario ya registrado: si el DNI o el email
   ya existen en `usuarios`, aborta con error sin modificar la base.
2. No acepta la contrasena como argumento de linea de comandos para no exponerla
   en el historial de shell ni en la lista de procesos: la lee exclusivamente de
   la variable de entorno ``ADMIN_TEST_PASSWORD``.
3. Por defecto solo permite bases de prueba. Para usar deliberadamente la base
   local de desarrollo ``centro_medico`` en ``127.0.0.1:3306`` exige el flag
   adicional ``--confirmar-base-desarrollo-local`` y valida exactamente host,
   puerto y schema. Nunca acepta un host remoto con ese flag.

Uso recomendado sobre una instancia MySQL temporal aislada (ej. puerto 3307):

    cd backend
    DB_HOST=127.0.0.1 DB_PORT=3307 DB_NAME=centro_medico \\
    ADMIN_TEST_PASSWORD="<clave_de_prueba_min_8_caracteres>" \\
    ./.venv/bin/python db/crear_admin_prueba.py \\
        --confirmar-base-prueba \\
        --email admin@saludintegral.com \\
        --dni 11222333 \\
        --nombre Admin \\
        --apellido Sistema
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402
import mysql.connector  # noqa: E402
from mysql.connector import errorcode  # noqa: E402

from app.constants import ROL_ADMIN  # noqa: E402
from app.db import get_connection  # noqa: E402
from app.services.auth_service import generar_hash_canonico  # noqa: E402
from app.validators.auth_validators import validar_payload_registro_paciente  # noqa: E402

HOSTS_LOCALES_PERMITIDOS = frozenset({"localhost", "127.0.0.1", "::1"})
SUFIJOS_DB_PRUEBA = ("_test", "_prueba", "_tmp", "_e2e")


class ErrorSeguridadBasePrueba(RuntimeError):
    """Se lanza cuando el destino MySQL no cumple la barrera de base de prueba."""


class UsuarioExistenteError(ValueError):
    """Se lanza cuando el DNI o el correo ya existen en la tabla ``usuarios``."""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Crea un usuario nuevo con rol='admin' en una base MySQL local de prueba o desarrollo "
            "usando el hasher canonico del proyecto (pbkdf2:sha256:600000). "
            "Lee la contrasena desde la variable de entorno ADMIN_TEST_PASSWORD."
        )
    )
    parser.add_argument(
        "--confirmar-base-prueba",
        action="store_true",
        help=(
            "Confirma explicitamente que la base configurada en DB_HOST/DB_PORT/DB_NAME "
            "es un entorno de prueba aislado."
        ),
    )
    parser.add_argument(
        "--confirmar-base-desarrollo-local",
        action="store_true",
        help=(
            "Permite explícitamente insertar una cuenta nueva en la base local "
            "centro_medico de 127.0.0.1:3306. No modifica cuentas existentes."
        ),
    )
    parser.add_argument(
        "--email",
        default=os.getenv("ADMIN_TEST_EMAIL", "admin@saludintegral.com"),
        help="Correo electronico de la cuenta admin nueva (default: admin@saludintegral.com).",
    )
    parser.add_argument(
        "--dni",
        default=os.getenv("ADMIN_TEST_DNI", "11222333"),
        help="DNI numerico de 7 u 8 digitos (default: 11222333).",
    )
    parser.add_argument(
        "--nombre",
        default=os.getenv("ADMIN_TEST_NOMBRE", "Admin"),
        help="Nombre del usuario admin de prueba (default: Admin).",
    )
    parser.add_argument(
        "--apellido",
        default=os.getenv("ADMIN_TEST_APELLIDO", "Sistema"),
        help="Apellido del usuario admin de prueba (default: Sistema).",
    )
    return parser.parse_args()


def verificar_barrera_base_prueba(
    *,
    confirmado: bool,
    db_host: str,
    db_port: str,
    db_name: str,
    confirmar_base_desarrollo_local: bool = False,
) -> None:
    """Exige confirmación y restringe estrictamente los destinos permitidos."""
    host_limpio = db_host.strip().lower()
    nombre_limpio = db_name.strip().lower()

    if confirmar_base_desarrollo_local:
        if not confirmado:
            raise ErrorSeguridadBasePrueba(
                "Barrera de seguridad: confirma el uso de la base local con "
                "--confirmar-base-desarrollo-local."
            )
        if host_limpio not in HOSTS_LOCALES_PERMITIDOS:
            raise ErrorSeguridadBasePrueba(
                "Barrera de seguridad: la base de desarrollo solo se permite en un host local."
            )
        try:
            puerto = int(db_port)
        except ValueError as exc:
            raise ErrorSeguridadBasePrueba(
                f"Barrera de seguridad: DB_PORT='{db_port}' no es un entero valido."
            ) from exc
        if puerto != 3306 or nombre_limpio != "centro_medico":
            raise ErrorSeguridadBasePrueba(
                "Barrera de seguridad: --confirmar-base-desarrollo-local solo permite "
                "127.0.0.1/localhost:3306/centro_medico."
            )
        return

    if not confirmado:
        raise ErrorSeguridadBasePrueba(
            "Barrera de seguridad: debes pasar --confirmar-base-prueba para ejecutar este script."
        )

    if host_limpio not in HOSTS_LOCALES_PERMITIDOS:
        raise ErrorSeguridadBasePrueba(
            f"Barrera de seguridad: DB_HOST='{db_host}' no es un host local permitido "
            f"({', '.join(sorted(HOSTS_LOCALES_PERMITIDOS))})."
        )

    try:
        puerto = int(db_port)
    except ValueError as exc:
        raise ErrorSeguridadBasePrueba(
            f"Barrera de seguridad: DB_PORT='{db_port}' no es un entero valido."
        ) from exc

    es_schema_prueba = nombre_limpio.endswith(SUFIJOS_DB_PRUEBA)
    es_instancia_temporal = puerto != 3306

    if not es_schema_prueba and not es_instancia_temporal:
        raise ErrorSeguridadBasePrueba(
            "Barrera de seguridad: se rechazo la ejecucion sobre "
            f"{db_host}:{puerto}/{db_name} porque coincide con el puerto estandar 3306 "
            "y un nombre de schema sin sufijo de prueba. Usa una instancia MySQL temporal "
            "en otro puerto (ej. DB_PORT=3307) o un schema terminado en _test / _prueba."
        )


def crear_admin_nuevo_prueba(
    *,
    dni: str,
    nombre: str,
    apellido: str,
    email: str,
    password: str,
) -> dict[str, object]:
    """Inserta un usuario administrativo nuevo en ``usuarios`` sin modificar filas existentes."""
    datos_validados, error_msg = validar_payload_registro_paciente(
        {
            "dni": dni,
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "password": password,
        }
    )
    if error_msg is not None or datos_validados is None:
        raise ValueError(error_msg or "Datos invalidos para la cuenta admin de prueba.")

    password_hash = generar_hash_canonico(datos_validados["password"])

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, dni, email, rol
            FROM usuarios
            WHERE email = %s OR dni = %s
            LIMIT 1
            """,
            (datos_validados["email"], datos_validados["dni"]),
        )
        existente = cursor.fetchone()
        if existente is not None:
            connection.rollback()
            raise UsuarioExistenteError(
                "No se modifico ninguna cuenta: ya existe un usuario con "
                f"dni={existente['dni']} o email={existente['email']} "
                f"(id={existente['id']}, rol={existente['rol']})."
            )

        cursor.execute(
            """
            INSERT INTO usuarios (dni, nombre, apellido, email, password_hash, rol, activo)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
            """,
            (
                datos_validados["dni"],
                datos_validados["nombre"],
                datos_validados["apellido"],
                datos_validados["email"],
                password_hash,
                ROL_ADMIN,
            ),
        )
        id_usuario = int(cursor.lastrowid)
        connection.commit()
    except UsuarioExistenteError:
        raise
    except mysql.connector.IntegrityError as exc:
        connection.rollback()
        if exc.errno == errorcode.ER_DUP_ENTRY:
            raise UsuarioExistenteError(
                "No se modifico ninguna cuenta: el DNI o el correo ya estan registrados."
            ) from exc
        raise
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    return {
        "accion": "creado",
        "id_usuario": id_usuario,
        "dni": datos_validados["dni"],
        "email": datos_validados["email"],
        "rol": ROL_ADMIN,
    }


def main() -> int:
    load_dotenv(BACKEND_DIR / ".env", override=False)
    args = _parse_args()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "centro_medico")

    try:
        if args.confirmar_base_prueba and args.confirmar_base_desarrollo_local:
            raise ErrorSeguridadBasePrueba(
                "Usa solo uno de estos flags: --confirmar-base-prueba o "
                "--confirmar-base-desarrollo-local."
            )
        verificar_barrera_base_prueba(
            confirmado=bool(args.confirmar_base_prueba or args.confirmar_base_desarrollo_local),
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            confirmar_base_desarrollo_local=bool(args.confirmar_base_desarrollo_local),
        )
    except ErrorSeguridadBasePrueba as exc:
        print(str(exc), file=sys.stderr)
        return 2

    password = os.getenv("ADMIN_TEST_PASSWORD", "")
    if not password:
        print(
            "Error: debes definir la variable de entorno ADMIN_TEST_PASSWORD "
            "(minimo 8 caracteres). Por seguridad no se acepta por linea de comandos.",
            file=sys.stderr,
        )
        return 2

    try:
        resultado = crear_admin_nuevo_prueba(
            dni=args.dni,
            nombre=args.nombre,
            apellido=args.apellido,
            email=args.email,
            password=password,
        )
    except UsuarioExistenteError as exc:
        print(f"Error de cuenta duplicada: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error de validacion: {exc}", file=sys.stderr)
        return 2

    print(
        f"Usuario admin de prueba {resultado['accion']} en {db_host}:{db_port}/{db_name}: "
        f"id_usuario={resultado['id_usuario']}, dni={resultado['dni']}, "
        f"email={resultado['email']}, rol={resultado['rol']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
