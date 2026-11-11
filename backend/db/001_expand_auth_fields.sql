-- Actualiza instalaciones existentes al contrato de autenticación.
-- La modificación conserva NOT NULL y el índice UNIQUE de usuarios.email.
USE centro_medico;

ALTER TABLE usuarios
    MODIFY COLUMN email VARCHAR(254) NOT NULL,
    MODIFY COLUMN password_hash VARCHAR(255) NOT NULL;