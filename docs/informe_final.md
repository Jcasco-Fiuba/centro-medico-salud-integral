# Proyecto Integrador: Centro Médico Salud Integral

## Carátula
- **Materia:** Introducción al Desarrollo de Software (Cátedra Lanzillotta)
- **Cuatrimestre:** 2do Cuatrimestre 2026
- **Grupo:** 18 - Seguidores del Loro Matteoli & larp

## Integrantes
- Jorge David Casco Coronel (116199)
- Josefina Abril Najar Gacek (113354)
- Alan Nieves Villagra (113133)
- Jorge Bencomo Navas (116303)
- Federico Nahuel Gioda (116480)
- Valentina Nieto (109046)
- Nicolás Galizio (116617)
- Cristopher Silva (116121)
- Lorenzo Decillo (116418)

## Resumen
Plataforma web para la gestión de agendas médicas, reserva de turnos online y control de asistencia mediante códigos QR, orientada a optimizar el flujo de pacientes y reducir el ausentismo en el Centro Médico Salud Integral.

## Introducción
El Centro Médico Salud Integral necesita una herramienta que centralice la gestión de agendas, turnos y llegada de pacientes. La solución propuesta permite consultar disponibilidad, reservar y cancelar turnos, confirmar la llegada mediante un código QR y ofrecer a recepción una sala de espera ordenada. Además, el personal administrativo puede mantener los catálogos del centro y consultar indicadores de ocupación y ausentismo.

El alcance inicial se limita a la gestión de turnos y atención ambulatoria. No incluye historia clínica, facturación, pagos, recetas ni videconsultas. La planificación detallada del Hito 1, con requisitos, reglas de negocio, casos de uso, riesgos y decisiones pendientes, se encuentra en `docs/hito1_plan.md`.

## Solución propuesta
Sistema compuesto por un Frontend de acceso a pacientes y un Backoffice de acceso administrativo, interconectados mediante una API RESTful desarrollada en Python con Flask. Se implementa un modelo de check-in automatizado escaneando un código QR generado al momento de reservar el turno dentro de una ventana horaria permitida.

## Tecnología utilizada
- **Backend:** Python, Flask, librerías estándar (sin utilización de ORMs).
- **Frontend:** Flask, HTML, CSS, Jinja, librería `requests` para comunicación con la API.
- **Base de Datos:** MySQL.
- **Infraestructura:** Docker, GitHub Projects (Scrum/Kanban).

## Conclusión final
[A completar al finalizar el Hito 7]