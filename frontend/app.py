"""Aplicación Flask del frontend del Centro Médico Salud Integral."""

import logging
import os
from pathlib import Path
import secrets

from flask import Flask

from routes import register_blueprints
from services.session_store import (
    DEFAULT_SESSION_LIFETIME_SECONDS,
    FileSystemSessionInterface,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
MIN_SECRET_KEY_LEN = 32


def _cargar_dotenv_local(env_path: Path) -> None:
    """Carga variables desde `frontend/.env` si existe, sin sobrescribir el entorno."""
    if not env_path.is_file():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


def _obtener_secret_key_estable(session_dir: Path) -> str:
    """Obtiene `FRONTEND_SECRET_KEY` estable desde el entorno o archivo persistente local.

    Nunca genera una clave efímera distinta por cada llamada a `create_app()`,
    evitando que se invaliden las sesiones activas al reiniciar el proceso.
    """
    secret_key = os.getenv("FRONTEND_SECRET_KEY", "").strip()
    if secret_key:
        if len(secret_key) < MIN_SECRET_KEY_LEN:
            raise RuntimeError(
                f"FRONTEND_SECRET_KEY debe tener al menos {MIN_SECRET_KEY_LEN} caracteres."
            )
        return secret_key

    if os.getenv("FLASK_ENV", "").strip().lower() == "production":
        raise RuntimeError(
            "FRONTEND_SECRET_KEY es obligatoria en producción y debe definirse en el entorno."
        )

    session_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    key_file = session_dir / ".secret_key"
    if key_file.is_file():
        stored = key_file.read_text(encoding="utf-8").strip()
        if len(stored) >= MIN_SECRET_KEY_LEN:
            return stored

    generated = secrets.token_hex(32)
    key_file.write_text(generated, encoding="utf-8")
    try:
        os.chmod(key_file, 0o600)
    except OSError:
        pass
    logger.warning(
        "FRONTEND_SECRET_KEY no está definida en el entorno; se inicializó una clave "
        "persistente local en %s. Configurá FRONTEND_SECRET_KEY en frontend/.env.",
        key_file,
    )
    return generated


def create_app() -> Flask:
    _cargar_dotenv_local(BASE_DIR / ".env")

    app = Flask(__name__)

    session_dir = Path(
        os.getenv("FRONTEND_SESSION_DIR", str(BASE_DIR / ".flask_session"))
    ).resolve()
    session_ttl = int(
        os.getenv("FRONTEND_SESSION_TTL", str(DEFAULT_SESSION_LIFETIME_SECONDS))
    )
    cookie_secure = os.getenv("FRONTEND_COOKIE_SECURE", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    app.secret_key = _obtener_secret_key_estable(session_dir)
    app.config["SESSION_COOKIE_NAME"] = "cmsi_session"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = cookie_secure

    app.session_interface = FileSystemSessionInterface(
        storage_dir=session_dir,
        default_ttl=session_ttl,
    )

    register_blueprints(app)
    return app


if __name__ == "__main__":
    port = int(os.getenv("FRONTEND_PORT", "5001"))
    create_app().run(debug=True, port=port)
