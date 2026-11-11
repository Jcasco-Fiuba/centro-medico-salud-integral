"""Registro central de blueprints del backend."""

from importlib import import_module

from flask import Blueprint, Flask

from app.routes.auth import auth_api_bp
from app.routes.pacientes import pacientes_bp

# Módulos opcionales de otras ramas para facilitar la integración centralizada
# sin registrar ningún blueprint dos veces.
_BLUEPRINTS_OPCIONALES: tuple[tuple[str, str], ...] = (
    ("app.routes.consultorios", "consultorios_bp"),
    ("app.routes.medicos_especialidades", "especialidades_bp"),
    ("app.routes.medicos", "medicos_bp"),
    ("app.routes.turnos", "turnos_bp"),
)


def _registrar_si_no_existe(app: Flask, bp: Blueprint) -> None:
    if bp.name not in app.blueprints:
        app.register_blueprint(bp)


def register_blueprints(app: Flask) -> None:
    """Registra los blueprints disponibles de la API una única vez."""
    _registrar_si_no_existe(app, pacientes_bp)
    _registrar_si_no_existe(app, auth_api_bp)

    for module_path, attr_name in _BLUEPRINTS_OPCIONALES:
        try:
            module = import_module(module_path)
        except ImportError:
            continue
        bp = getattr(module, attr_name, None)
        if isinstance(bp, Blueprint):
            _registrar_si_no_existe(app, bp)
