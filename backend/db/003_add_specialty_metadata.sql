-- Agrega los campos usados por el CRUD actual de especialidades
-- a instalaciones existentes sin borrar ni volver a insertar datos.
USE centro_medico;

ALTER TABLE especialidades
    ADD COLUMN descripcion VARCHAR(256) NULL AFTER nombre,
    ADD COLUMN activo BOOLEAN DEFAULT TRUE AFTER descripcion;
