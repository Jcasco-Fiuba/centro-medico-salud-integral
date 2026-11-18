"""Servicios de negocio del backend."""

from app.services.auth_service import (
    CredencialesInvalidasError,
    EstadoPacienteConflictoError,
    PacienteNoEncontradoError,
    PermisoDenegadoError,
    UsuarioDuplicadoError,
    actualizar_perfil_paciente,
    autenticar_usuario,
    dar_baja_logica_paciente,
    generar_hash_canonico,
    listar_pacientes_registrados,
    obtener_perfil_paciente,
    obtener_usuario_autenticado_desde_header,
    registrar_paciente,
    requiere_autenticacion,
    verificar_password_almacenada,
)
from app.services.jwt_service import (
    JWTConfigError,
    TokenInvalidoError,
    decodificar_y_validar_token,
    extraer_bearer_token,
    generar_access_token,
)

__all__ = [
    "CredencialesInvalidasError",
    "EstadoPacienteConflictoError",
    "JWTConfigError",
    "PacienteNoEncontradoError",
    "PermisoDenegadoError",
    "TokenInvalidoError",
    "UsuarioDuplicadoError",
    "actualizar_perfil_paciente",
    "autenticar_usuario",
    "dar_baja_logica_paciente",
    "decodificar_y_validar_token",
    "extraer_bearer_token",
    "generar_access_token",
    "generar_hash_canonico",
    "listar_pacientes_registrados",
    "obtener_perfil_paciente",
    "obtener_usuario_autenticado_desde_header",
    "registrar_paciente",
    "requiere_autenticacion",
    "verificar_password_almacenada",
]
