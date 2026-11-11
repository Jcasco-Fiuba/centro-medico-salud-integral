"""Inicialización de la aplicación Flask del backend."""

from flask import Flask

from app.routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    register_blueprints(app)
    return app
