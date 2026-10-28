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