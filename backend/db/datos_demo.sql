-- turnos de prueba. ejecutar DESPUÉS de db.sql:
-- mysql -u root -p < backend/db/datos_demo.sql
USE centro_medico;

INSERT INTO turnos (id_usuario, id_medico, id_consultorio, fecha_hora, estado, string_token) VALUES
-- Laura Martinez (Clínica Medica): turnos libres
(NULL, 1, 1, '2026-11-27 09:00:00', 'disponible', NULL),
(NULL, 1, 1, '2026-11-27 09:30:00', 'disponible', NULL),
(NULL, 1, 1, '2026-12-01 09:00:00', 'disponible', NULL),
(NULL, 1, 1, '2026-12-01 09:30:00', 'disponible', NULL),
(NULL, 1, 1, '2026-12-09 10:00:00', 'disponible', NULL),
(NULL, 1, 1, '2026-12-09 10:30:00', 'disponible', NULL),
-- Anabel Ruiz (Pediatria): turnos libres
(NULL, 2, 2, '2026-11-28 14:00:00', 'disponible', NULL),
(NULL, 2, 2, '2026-11-28 14:30:00', 'disponible', NULL),
(NULL, 2, 2, '2026-12-02 14:00:00', 'disponible', NULL),
(NULL, 2, 2, '2026-12-02 14:30:00', 'disponible', NULL),
(NULL, 2, 2, '2026-12-10 16:00:00', 'disponible', NULL),
(NULL, 2, 2, '2026-12-10 16:30:00', 'disponible', NULL),
-- Marta: turno reservado con Anabel que se puede cancelar
(1, 2, 2, '2026-12-11 15:00:00', 'reservado', 'DEMO-CANCELAR');