#!/bin/bash
echo "=============================================="
echo "Exportando Historial de Conversaciones..."
echo "=============================================="

# Obtener la ruta del directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/../../.."

if [ ! -d "backend/.venv" ]; then
    echo "ERROR: El entorno virtual backend/.venv no existe. Por favor ejecuta venv.sh primero."
    exit 1
fi

echo "Ejecutando export_conversations.py..."
backend/.venv/bin/python scripts/chats/gemini/export_conversations.py

echo "Compilando sitio de documentación con MkDocs..."
backend/.venv/bin/mkdocs build

echo "=============================================="
echo "¡Historial exportado y documentación compilada con éxito!"
echo "=============================================="
