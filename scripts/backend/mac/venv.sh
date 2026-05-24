#!/bin/bash
echo "=============================================="
echo "Instalando Entorno Virtual y Dependencias..."
echo "=============================================="

# Obtener la ruta del directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/../../.."

# Verificar si python3 está instalado
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python no está instalado o no se encuentra en el PATH."
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Crear entorno virtual si no existe
if [ ! -d "backend/.venv" ]; then
    echo "Creando entorno virtual backend/.venv..."
    $PYTHON_CMD -m venv backend/.venv
else
    echo "El entorno virtual backend/.venv ya existe."
fi

# Activar e instalar requerimientos
echo "Instalando dependencias desde requirements.txt..."
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

echo
echo "=============================================="
echo "¡Instalación completada exitosamente!"
echo "=============================================="
