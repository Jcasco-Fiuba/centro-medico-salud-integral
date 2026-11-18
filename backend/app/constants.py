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
