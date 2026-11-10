"""Cliente server-side para comunicarse con la API usando requests."""

import os

import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
TIMEOUT = 10

def enviar(metodo, ruta, datos=None):
    """Hace la llamada a la API y devuelve la respuesta y el status."""
    try:
        respuesta = requests.request(metodo, API_URL + ruta, json=datos, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        return {"error": "No se pudo conectar con el servidor"}, 503

    try:
        contenido = respuesta.json()
    except ValueError:
        contenido = {"error": "La respuesta del servidor no es valida"}

    return contenido, respuesta.status_code

def get(ruta):
    """Hace un GET a la API."""
    return enviar("GET", ruta)

def post(ruta, datos=None):
    """Hace un POST a la API."""
    return enviar("POST", ruta, datos)

def patch(ruta, datos=None):
    """Hace un PATCH a la API."""
    return enviar("PATCH", ruta, datos)
