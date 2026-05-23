@echo off
echo ==============================================
echo Configurando Alias para la Consola (CMD)...
echo ==============================================

doskey install="%~dp0install.bat"
doskey run="%~dp0run.bat"
doskey export="%~dp0export.bat"

echo Alias creados exitosamente para esta sesion de CMD:
echo   - install  : Ejecuta scripts/install.bat (instala entorno y dependencias)
echo   - run      : Ejecuta scripts/run.bat (inicia el servidor de FastAPI)
echo   - export   : Ejecuta scripts/export.bat (exporta el historial de chats a markdown)
echo.
echo NOTA: Para hacer uso de los alias "install", "run" y "export", debes
echo ejecutar este archivo setup_aliases.bat una vez en tu ventana de CMD.
echo ==============================================
