# Backend

API REST desarrollada con Flask (`http://127.0.0.1:5000` por defecto). Las
consultas a MySQL se implementan con sentencias SQL explícitas y parametrizadas
mediante MySQL Connector/Python; el proyecto no usa ORM.

## Requisitos

- Python 3
- MySQL 8.x o MariaDB disponible localmente
- Bash (por ejemplo, WSL en Windows)

## Base de datos de prueba aislada (antes de iniciar)

> **Importante:** `backend/db/db.sql` incluye al comienzo las sentencias
> `CREATE DATABASE IF NOT EXISTS centro_medico;` y `USE centro_medico;`. Nunca
> ejecutes `mysql ... < backend/db/db.sql` directamente contra una instancia que
> contenga una base personal llamada `centro_medico`, porque `USE centro_medico;`
> seleccionaría ese schema.

Elegí una de estas dos opciones de aislamiento:

### Opción A (recomendada): Instancia MySQL temporal en puerto y socket propios

Crea un servidor MySQL temporal en `/tmp/mysql_cmsi_test` (puerto `3307`),
totalmente separado del servicio MySQL del sistema (`3306`):

```bash
mkdir -p /tmp/mysql_cmsi_test/data /tmp/mysql_cmsi_test/run
mysqld --no-defaults --initialize-insecure \
  --datadir=/tmp/mysql_cmsi_test/data \
  --user="$(whoami)"

mysqld --no-defaults \
  --datadir=/tmp/mysql_cmsi_test/data \
  --socket=/tmp/mysql_cmsi_test/run/mysqld.sock \
  --pid-file=/tmp/mysql_cmsi_test/run/mysqld.pid \
  --port=3307 --bind-address=127.0.0.1 \
  --mysqlx=0 --skip-log-bin \
  --user="$(whoami)" > /tmp/mysql_cmsi_test/mysqld.log 2>&1 &

# Cargar el esquema y los datos iniciales en el schema `centro_medico` de la instancia 3307
mysql --protocol=SOCKET --socket=/tmp/mysql_cmsi_test/run/mysqld.sock -u root < backend/db/db.sql
```

En `backend/.env` configurá `DB_HOST=127.0.0.1`, `DB_PORT=3307`, `DB_USER=root`,
`DB_PASSWORD=` y `DB_NAME=centro_medico`.

Para detener la instancia temporal y limpiar sus archivos al terminar:

```bash
mysqladmin --protocol=SOCKET --socket=/tmp/mysql_cmsi_test/run/mysqld.sock -u root shutdown
rm -rf /tmp/mysql_cmsi_test
```

### Opción B: Schema separado dentro de un servidor MySQL local

Si usás un servidor MySQL local pero querés cargar el esquema en una base de
prueba separada (por ejemplo `centro_medico_test`) sin que `USE centro_medico;`
afecte a otra base:

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS centro_medico_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sed -E '/^(CREATE DATABASE|USE) centro_medico;/d' backend/db/db.sql | mysql -u root -p -D centro_medico_test
```

Luego configurá `DB_NAME=centro_medico_test` en `backend/.env`.

## Cuentas de prueba y creación reproducible de un usuario `admin`

- `backend/db/db.sql` carga únicamente **dos pacientes demo**:
  - `marta@gomez.com` / `12345678` (`dni`: `99999999`, `id`: `1`, `rol`: `paciente`)
  - `juan@perez.com` / `juan5555` (`dni`: `55555555`, `id`: `2`, `rol`: `paciente`)
- Por seguridad, `db.sql` **no incluye una cuenta `admin` con clave fija**. Para
  probar rutas de recepción y administración en la base de prueba, ejecutá el
  script [`db/crear_admin_prueba.py`](./db/crear_admin_prueba.py), que solo
  inserta cuentas nuevas (falla sin modificar nada si el DNI o email ya existen),
  exige `--confirmar-base-prueba` y lee la contraseña desde la variable de
  entorno `ADMIN_TEST_PASSWORD` (sin exponerla como argumento en la terminal):

```bash
cd backend
DB_HOST=127.0.0.1 DB_PORT=3307 DB_NAME=centro_medico \
ADMIN_TEST_PASSWORD="<tu_clave_de_prueba_min_8_chars>" \
./.venv/bin/python db/crear_admin_prueba.py \
  --confirmar-base-prueba \
  --email admin@saludintegral.com \
  --dni 11222333 \
  --nombre Admin \
  --apellido Sistema
```

## Inicio del servidor Backend (puerto 5000)

Desde la raíz del repositorio:

```bash
cd backend
bash ./init.sh
```

La primera ejecución crea el entorno virtual `.venv`, instala las dependencias
y copia `.env.example` a `.env`. Editá `backend/.env` con la conexión a la base
de prueba y `JWT_SECRET_KEY`. El servidor inicia en `http://127.0.0.1:5000`.

También se puede preparar e iniciar manualmente:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Configurar JWT_SECRET_KEY (mínimo 32 caracteres) y DB_* en .env
python app.py
```

## Configuración (`backend/.env`)

Variables definidas en [`backend/.env.example`](./.env.example):

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` y
  `DB_CONNECT_TIMEOUT`: parámetros de conexión a MySQL.
- `API_PORT`: puerto del backend (por defecto `5000`).
- `JWT_SECRET_KEY`: clave secreta exclusiva de al menos 32 caracteres (por
  ejemplo generada con `python3 -c "import secrets; print(secrets.token_hex(32))"`).
- `JWT_EXPIRATION_SECONDS`: tiempo de vida del token en segundos (por defecto
  `3600`, equivalente a 1 hora).

## Consultas SQL

Usá cursores de MySQL Connector y parámetros enlazados (`%s`), por ejemplo:

```python
connection = get_connection()
try:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre FROM especialidades WHERE id = %s", (1,))
    rows = cursor.fetchall()
finally:
    cursor.close()
    connection.close()
```

No interpolar valores recibidos en una cadena SQL. Para operaciones de escritura,
confirmá la transacción con `connection.commit()` y revertí errores con
`connection.rollback()` antes de cerrar.
