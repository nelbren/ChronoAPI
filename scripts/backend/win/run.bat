@echo off
echo ==============================================
echo Iniciando Servidor ChronoAPI con FastAPI...
echo ==============================================
cd /d "%~dp0..\..\.."

if not exist backend\.venv (
    echo ERROR: El entorno virtual backend\.venv no existe. Por favor ejecuta venv.bat primero.
    pause
    exit /b 1
)

echo Iniciando uvicorn...
call backend\.venv\Scripts\python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
