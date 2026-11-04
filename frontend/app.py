"""Aplicación Flask del frontend del Centro Médico Salud Integral."""

import os

from flask import Flask

from routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    register_blueprints(app)
    return app


if __name__ == "__main__":
    port = int(os.getenv("FRONTEND_PORT", "5001"))
    create_app().run(debug=True, port=port)
