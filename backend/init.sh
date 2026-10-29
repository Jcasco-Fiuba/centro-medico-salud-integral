#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf 'No se encontró %s. Instalá Python 3 y volvé a ejecutar este script.\n' "$PYTHON_BIN" >&2
    exit 1
fi

if [[ ! -d .venv ]]; then
    "$PYTHON_BIN" -m venv .venv
fi

# La ruta del entorno virtual se calcula en tiempo de ejecución.
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [[ ! -f .env ]]; then
    cp .env.example .env
    printf 'Se creó backend/.env. Revisá la configuración de MySQL antes de usar rutas que consulten la base.\n'
fi

exec python app.py
