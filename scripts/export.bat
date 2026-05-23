@echo off
echo ==============================================
echo Exportando Historial de Conversaciones...
echo ==============================================
cd /d "%~dp0.."

if not exist .venv (
    echo ERROR: El entorno virtual .venv no existe. Por favor ejecuta install primero.
    pause
    exit /b 1
)

echo Ejecutando export_conversations.py...
call .venv\Scripts\python scripts\export_conversations.py
echo ==============================================
echo ¡Historial exportado y ordenado con éxito!
echo ==============================================
