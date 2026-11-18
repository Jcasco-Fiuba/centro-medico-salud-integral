-- Actualiza unicamente las dos cuentas demo conocidas si conservan el seed en claro.
-- No habilita validacion de contrasenas en texto plano en el backend.
USE centro_medico;

UPDATE usuarios
SET password_hash = 'pbkdf2:sha256:600000$Kohtf8RSnLoH$2b6b7cebbb5f5cbb77539d2582cc0bcb68881cc4f5cb077c3dfcba8c9c9e742c'
WHERE dni = '99999999' AND email = 'marta@gomez.com' AND password_hash = '12345678';

UPDATE usuarios
SET password_hash = 'pbkdf2:sha256:600000$8TgUqa4duR6l$ba13553f7437e874ce3a91085916b9acb18d09bc7cea3191fb01d2248bfb41b8'
WHERE dni = '55555555' AND email = 'juan@perez.com' AND password_hash = 'juan5555';