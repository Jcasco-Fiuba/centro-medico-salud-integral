# Esquema y migraciones de la base de datos

## Instalación nueva

Ejecutar `db.sql`. El script crea las tablas y carga datos de prueba con hashes
PBKDF2-SHA256 compatibles con el servicio de autenticación.

## Base existente

Ejecutar, en este orden y una sola vez por instalación:

1. `001_expand_auth_fields.sql`: amplía `usuarios.email` a 254 caracteres y
   `usuarios.password_hash` a 255.
2. `002_hash_legacy_demo_passwords.sql`: reemplaza las contraseñas en claro de
   las dos cuentas demo conocidas, únicamente si aún conservan esos valores.

El backend no debe aceptar contraseñas en texto plano como mecanismo de
compatibilidad. Si existen otras cuentas con contraseñas en claro, deben
restablecerse mediante un flujo seguro o una migración controlada; no se deben
copiar esos valores a una consulta de login.