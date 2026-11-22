# Esquema, migraciones y datos de prueba de la base de datos

## Aviso sobre `CREATE DATABASE` y `USE centro_medico`

Los scripts `db.sql` y las migraciones `001_expand_auth_fields.sql`,
`002_hash_legacy_demo_passwords.sql` y `003_add_specialty_metadata.sql` contienen
la directiva `USE centro_medico;`.

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
dos usuarios de rol `paciente` (`marta@gomez.com` / `12345678`,
`juan@perez.com` / `juan5555`) y uno de rol `admin`
(`admin@saludintegral.com` / `Admin1234`), cuyos hashes usan el formato canónico
`pbkdf2:sha256:600000` (98 caracteres).

## Base existente (migraciones incrementales)

Si una base fue creada con una revisión previa del esquema, ejecutar en este
orden y una sola vez:

1. `001_expand_auth_fields.sql`: amplía `usuarios.email` a `VARCHAR(254)` y
   `usuarios.password_hash` a `VARCHAR(255)`.
2. `002_hash_legacy_demo_passwords.sql`: reemplaza las contraseñas en claro de
   las dos cuentas demo de pacientes conocidas (`marta@gomez.com` y
   `juan@perez.com`), únicamente si aún conservan esos valores en texto plano.
3. `003_add_specialty_metadata.sql`: agrega `descripcion` y `activo` a
   `especialidades` sin borrar ni volver a insertar registros existentes.

> Si aplicás estas migraciones sobre un schema con otro nombre (por ejemplo
> `centro_medico_test`), filtrá `USE centro_medico;`:
> ```bash
> sed '/^USE centro_medico;/d' backend/db/001_expand_auth_fields.sql | mysql -u root -p -D centro_medico_test
> sed '/^USE centro_medico;/d' backend/db/002_hash_legacy_demo_passwords.sql | mysql -u root -p -D centro_medico_test
> sed '/^USE centro_medico;/d' backend/db/003_add_specialty_metadata.sql | mysql -u root -p -D centro_medico_test
> ```

El backend nunca acepta contraseñas en texto plano como mecanismo de
compatibilidad.

## Cuenta `admin` de prueba

`db.sql` crea una cuenta de administrador para pruebas, junto con los dos
pacientes demo:

- `admin@saludintegral.com` / `Admin1234` (`dni`: `11222333`, `id`: `3`, `rol`: `admin`)

Como en los pacientes, la contraseña se guarda solo como hash
`pbkdf2:sha256:600000`; el script nunca contiene la clave en texto plano.

Para volver a cargar la base desde cero (borra todos los datos cargados a mano):

```bash
mysql -u root -p -e "DROP DATABASE centro_medico;"
mysql -u root -p < backend/db/db.sql
```

- **En una instalación real:** el administrador inicial debe crearse con datos
  reales y una contraseña robusta generada para ese entorno, nunca con la clave
  de prueba `Admin1234`.
