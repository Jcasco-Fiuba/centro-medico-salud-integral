"""Conexiones a MySQL mediante MySQL Connector/Python y SQL explícito."""

import mysql.connector
from mysql.connector import MySQLConnection

from app.constants import (
    DB_CONNECT_TIMEOUT,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)


def get_connection() -> MySQLConnection:
    """Abre una conexión a MySQL con la configuración del entorno.

    Quien use esta función debe cerrar la conexión al terminar. Las consultas
    deben usar parámetros de Connector/Python (marcadores ``%s``), sin interpolar
    texto ni recurrir a un ORM.
    """
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connection_timeout=DB_CONNECT_TIMEOUT,
        charset="utf8mb4",
        use_unicode=True,
        autocommit=False,
    )
