"""Registro de blueprints del frontend."""

from routes.administracion import administracion_bp
from routes.auth import auth_bp
from routes.paciente import paciente_bp
from routes.public import public_bp
from routes.recepcion import recepcion_bp


def register_blueprints(app) -> None:
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(paciente_bp)
    app.register_blueprint(recepcion_bp)
    app.register_blueprint(administracion_bp)
