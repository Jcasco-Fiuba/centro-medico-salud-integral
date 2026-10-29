# Backend

API REST desarrollada con Flask. Las consultas a MySQL se implementan con
sentencias SQL explícitas mediante MySQL Connector/Python; el proyecto no usa
ORM.

## Requisitos

- Python 3
- MySQL o MariaDB disponible localmente
- Bash (por ejemplo, WSL en Windows)

## Inicio

Desde la raíz del repositorio:

```bash
cd backend
bash ./init.sh
```

La primera ejecución crea el entorno virtual `.venv`, instala las dependencias
y copia `.env.example` a `.env`. Editá `.env` con la configuración de tu
servidor MySQL. El script luego inicia Flask en `http://127.0.0.1:5000`.

También se puede preparar e iniciar manualmente:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Configuración

`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD` configuran la
conexión. `DB_CONNECT_TIMEOUT` define el tiempo máximo de espera. El servidor
local usa el puerto definido por `API_PORT` y activa el modo debug, como en el
proyecto anterior.

Las rutas que necesiten datos pueden usar `app.db.get_connection()` y deben
cerrar la conexión después de cada operación.

## Consultas SQL

Usá cursores de MySQL Connector y parámetros enlazados, por ejemplo:

```python
connection = get_connection()
try:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre FROM especialidades WHERE activo = %s", (1,))
    rows = cursor.fetchall()
finally:
    cursor.close()
    connection.close()
```

No interpolar valores recibidos en una cadena SQL. Para operaciones de escritura,
confirmá la transacción con `connection.commit()` y revertí errores con
`connection.rollback()` antes de cerrar.
