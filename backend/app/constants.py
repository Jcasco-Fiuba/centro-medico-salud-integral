import os

from dotenv import load_dotenv

load_dotenv()

# URL base de la API.
BASE_URL = "/api"

# Configuración de MySQL; los valores sensibles van en backend/.env.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "centro_medico")
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))

# Ajustes para ejecutar Flask en desarrollo local.
API_PORT = int(os.getenv("API_PORT", "5000"))

# Configuración de JWT; JWT_SECRET_KEY debe definirse en el entorno (sin secreto hardcodeado).
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = int(os.getenv("JWT_EXPIRATION_SECONDS", "3600"))
JWT_REMEMBER_EXPIRATION_SECONDS = int(os.getenv("JWT_REMEMBER_EXPIRATION_SECONDS", "604800"))
JWT_MIN_SECRET_LENGTH = 32

# Roles del sistema según la tabla unificada `usuarios`.
ROL_PACIENTE = "paciente"
ROL_ADMIN = "admin"
ROLES_VALIDOS = (ROL_PACIENTE, ROL_ADMIN)

# --- Email (Flask-Mail / SMTP) ---
# Si MAIL_USERNAME/MAIL_PASSWORD están vacíos o MAIL_SUPPRESS_SEND=true, no se
# envía nada: se loguea (modo dev/tests). Con Gmail, MAIL_PASSWORD es un
# "App Password" (no la clave de la cuenta).
MAIL_SERVER         = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT           = int(os.getenv("MAIL_PORT", "587"))
MAIL_USE_TLS        = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
MAIL_USE_SSL        = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
MAIL_USERNAME       = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD       = os.getenv("MAIL_PASSWORD", "")
# Remitente. Si se deja vacío, usa MAIL_USERNAME (Gmail exige que el from sea la
# cuenta autenticada).
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "") or MAIL_USERNAME
MAIL_SUPPRESS_SEND  = os.getenv("MAIL_SUPPRESS_SEND", "false").lower() == "true"