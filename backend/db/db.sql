CREATE DATABASE IF NOT EXISTS centro_medico;
USE centro_medico;

CREATE TABLE IF NOT EXISTS consultorios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    ubicacion VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS especialidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dni VARCHAR(8) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    rol ENUM('paciente', 'admin') DEFAULT 'paciente',
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS medicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    matricula VARCHAR(20) UNIQUE NOT NULL,
    id_consultorio INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_consultorio) REFERENCES consultorios(id)
);

CREATE TABLE IF NOT EXISTS medicos_especialidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_medico INT NOT NULL,
    id_especialidad INT NOT NULL,
    FOREIGN KEY (id_medico) REFERENCES medicos(id),
    FOREIGN KEY (id_especialidad) REFERENCES especialidades(id),
    UNIQUE (id_medico, id_especialidad)
);

CREATE TABLE IF NOT EXISTS turnos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL, -- NULL mientras estado = disponible
    id_medico INT NOT NULL,
    id_consultorio INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    estado ENUM('disponible', 'reservado', 'confirmado', 'atendido', 'cancelado', 'ausente') DEFAULT 'disponible',
    string_token VARCHAR(255) UNIQUE,
    hora_checkin DATETIME NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_medico) REFERENCES medicos(id),
    FOREIGN KEY (id_consultorio) REFERENCES consultorios(id)
);

-- Datos de prueba
INSERT INTO consultorios (nombre, ubicacion, activo) VALUES
('Consultorio 1', 'Sede Central', TRUE),
('Consultorio 2', 'Sede Flores', TRUE);

INSERT INTO especialidades (nombre) VALUES
('Clinica Medica'),
('Pediatria');

INSERT INTO usuarios (dni, nombre, apellido, email, password_hash, rol, activo) VALUES
('99999999', 'Marta', 'Gomez', 'marta@gomez.com', '12345678', 'paciente', TRUE),
('55555555', 'Juan', 'Perez', 'juan@perez.com', '', 'juan5555', TRUE);

INSERT INTO medicos (nombre, apellido, matricula, id_consultorio, activo) VALUES
('Laura', 'Martinez', '34444', 1, TRUE),
('Anabel', 'Ruiz', '20000', 2, TRUE);

INSERT INTO medicos_especialidades (id_medico, id_especialidad) VALUES
(1, 1),
(2, 2);

-- Un turno disponible y uno reservado (fechas relativas a hoy)
INSERT INTO turnos (id_usuario, id_medico, id_consultorio, fecha_hora, estado, string_token, hora_checkin) VALUES
(NULL, 1, 1, '2026-11-02 9:00:00', 'disponible', NULL, NULL),
(2, 2, 2, '2026-11-02 10:00:00', 'reservado', 'manzana', NULL);