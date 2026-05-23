@echo off
echo ==============================================
echo Iniciando Servidor ChronoAPI con FastAPI...
echo ==============================================
cd /d "%~dp0.."

if not exist .venv (
    echo ERROR: El entorno virtual .venv no existe. Por favor ejecuta install.bat primero.
    pause
    exit /b 1
)

echo Iniciando uvicorn...
call .venv\Scripts\python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
