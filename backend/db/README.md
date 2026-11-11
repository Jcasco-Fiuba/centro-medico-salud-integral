# Esquema, migraciones y datos de prueba de la base de datos

## Aviso sobre `CREATE DATABASE` y `USE centro_medico`

Los scripts `db.sql`, `001_expand_auth_fields.sql` y
`002_hash_legacy_demo_passwords.sql` contienen la directiva `USE centro_medico;`.

- **En una instancia MySQL temporal aislada** (por ejemplo levantando `mysqld` en
  un directorio temporal como `/tmp/mysql_cmsi_test` en el puerto `3307`),
  podés ejecutar directamente:
  ```bash
  mysql --protocol=SOCKET --socket=/tmp/mysql_cmsi_test/run/mysqld.sock -u root < backend/db/db.sql
  ```
  Esto crea y puebla el schema `centro_medico` únicamente dentro de esa instancia
  temporal, sin tocar el servidor MySQL habitual del sistema.
- **En un schema separado dentro de un servidor MySQL compartido** (por ejemplo
  `centro_medico_test`), filtrá las sentencias `CREATE DATABASE` y `USE` para no
  modificar un schema `centro_medico` preexistente:
  ```bash
  mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS centro_medico_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
  sed -E '/^(CREATE DATABASE|USE) centro_medico;/d' backend/db/db.sql | mysql -u root -p -D centro_medico_test
  ```

## Instalación nueva

Ejecutar `db.sql` siguiendo una de las opciones de aislamiento anteriores. El
script crea las tablas (`consultorios`, `especialidades`, `usuarios`, `medicos`,
`medicos_especialidades`, `turnos`) con `usuarios.email VARCHAR(254)` y
`usuarios.password_hash VARCHAR(255)`, y carga datos iniciales de prueba con
dos usuarios de rol `paciente` (`marta@gomez.com` / `12345678` y
`juan@perez.com` / `juan5555`) cuyos hashes usan el formato canónico
`pbkdf2:sha256:600000` (98 caracteres).

## Base existente (migraciones incrementales)

Si una base fue creada con una revisión previa del esquema, ejecutar en este
orden y una sola vez:

1. `001_expand_auth_fields.sql`: amplía `usuarios.email` a `VARCHAR(254)` y
   `usuarios.password_hash` a `VARCHAR(255)`.
2. `002_hash_legacy_demo_passwords.sql`: reemplaza las contraseñas en claro de
   las dos cuentas demo de pacientes conocidas (`marta@gomez.com` y
   `juan@perez.com`), únicamente si aún conservan esos valores en texto plano.

> Si aplicás estas migraciones sobre un schema con otro nombre (por ejemplo
> `centro_medico_test`), filtrá `USE centro_medico;`:
> ```bash
> sed '/^USE centro_medico;/d' backend/db/001_expand_auth_fields.sql | mysql -u root -p -D centro_medico_test
> sed '/^USE centro_medico;/d' backend/db/002_hash_legacy_demo_passwords.sql | mysql -u root -p -D centro_medico_test
> ```

El backend nunca acepta contraseñas en texto plano como mecanismo de
compatibilidad.

## Creación reproducible de una cuenta `admin` de prueba

`db.sql` no incluye usuarios con `rol = 'admin'` para evitar que una instalación
quede con credenciales administrativas fijas o débiles por defecto.

- **Para pruebas locales o automatizadas:** usá el script
  [`crear_admin_prueba.py`](./crear_admin_prueba.py), que solo crea una cuenta
  nueva (si el DNI o el correo ya existen, termina con error sin modificar la
  fila existente), exige `--confirmar-base-prueba` (verificando que no apunte a
  `centro_medico` en el puerto estándar `3306`) y lee la contraseña desde la
  variable de entorno `ADMIN_TEST_PASSWORD` para no dejarla en el historial de
  comandos:
  ```bash
  cd backend
  DB_HOST=127.0.0.1 DB_PORT=3307 DB_NAME=centro_medico \
  ADMIN_TEST_PASSWORD="<clave_de_prueba_min_8_caracteres>" \
  ./.venv/bin/python db/crear_admin_prueba.py \
    --confirmar-base-prueba \
    --email admin@saludintegral.com \
    --dni 11222333 \
    --nombre Admin \
    --apellido Sistema
  ```
- **En una instalación real:** el administrador inicial debe aprovisionarse con
  datos reales y una contraseña robusta generada específicamente para ese
  entorno, nunca reutilizando contraseñas de prueba.
