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
