@echo off
echo ==============================================
echo Instalando Entorno Virtual y Dependencias...
echo ==============================================
cd /d "%~dp0..\..\.."

:: Verificar si python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no se encuentra en el PATH.
    pause
    exit /b 1
)

:: Crear entorno virtual si no existe
if not exist backend\.venv (
    echo Creando entorno virtual backend\.venv...
    python -m venv backend\.venv
) else (
    echo El entorno virtual backend\.venv ya existe.
)

:: Activar e instalar requerimientos
echo Instalando dependencias desde requirements.txt...
call backend\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

echo.
echo ==============================================
echo Instalacion completada exitosamente!
echo ==============================================
pause
