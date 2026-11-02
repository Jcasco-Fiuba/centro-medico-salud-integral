import logging

from flask import Flask

from app.constants import API_PORT

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

app = Flask(__name__)
app.json.sort_keys = False

from app.routes.medicos import medicos_bp
app.register_blueprint(medicos_bp)

if __name__ == "__main__":
    app.run(debug=True, port=API_PORT)
