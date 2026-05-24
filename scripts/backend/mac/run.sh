#!/bin/bash
echo "=============================================="
echo "Iniciando Servidor ChronoAPI con FastAPI..."
echo "=============================================="

# Obtener la ruta del directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/../../.."

if [ ! -d "backend/.venv" ]; then
    echo "ERROR: El entorno virtual backend/.venv no existe. Por favor ejecuta venv.sh primero."
    exit 1
fi

echo "Iniciando uvicorn..."
backend/.venv/bin/python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
