@echo off
echo ==============================================
echo Exportando Historial de Conversaciones...
echo ==============================================
cd /d "%~dp0..\..\.."

if not exist backend\.venv (
    echo ERROR: El entorno virtual backend\.venv no existe. Por favor ejecuta venv.bat primero.
    pause
    exit /b 1
)

echo Ejecutando export_conversations.py...
call backend\.venv\Scripts\python scripts\chats\gemini\export_conversations.py

echo Compilando sitio de documentación con MkDocs...
call backend\.venv\Scripts\mkdocs build

echo ==============================================
echo ¡Historial exportado y documentación compilada con éxito!
echo ==============================================
