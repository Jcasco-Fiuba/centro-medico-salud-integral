import logging

from app import create_app
from app.constants import API_PORT

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=API_PORT)
