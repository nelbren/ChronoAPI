@echo off
echo ==============================================
echo Configurando Alias para la Consola (CMD)...
echo ==============================================

doskey CA_install="%~dp0venv.bat"
doskey CA_run="%~dp0run.bat"
doskey CA_export="%~dp0export.bat"

echo Alias creados exitosamente para esta sesion de CMD:
echo   - CA_install : Ejecuta scripts/backend/win/venv.bat (instala entorno y dependencias)
echo   - CA_run     : Ejecuta scripts/backend/win/run.bat (inicia el servidor de FastAPI)
echo   - CA_export  : Ejecuta scripts/backend/win/export.bat (exporta el historial de chats a markdown)
echo.
echo NOTA: Para hacer uso de los alias "CA_install", "CA_run" y "CA_export", debes
echo ejecutar este archivo alias.bat una vez en tu ventana de CMD.
echo ==============================================
