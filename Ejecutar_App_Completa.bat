@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "APP_DIR=%ROOT_DIR%App_Completa"
set "PRE_APP=%APP_DIR%\pre_app_check.py"
set "MAIN_APP=%APP_DIR%\main.pyw"

echo.
echo ==============================================
echo  Inicio App_Completa
echo ==============================================
echo.

set "BASE_PY="
set "VENV_DIR=%APP_DIR%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PYW=%VENV_DIR%\Scripts\pythonw.exe"

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if %ERRORLEVEL%==0 (
    set "BASE_PY=py -3"
    goto :python_found
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if %ERRORLEVEL%==0 (
    set "BASE_PY=python"
    goto :python_found
)

python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if %ERRORLEVEL%==0 (
    set "BASE_PY=python3"
    goto :python_found
)

echo [ERROR] No se encontro Python instalado o disponible en PATH.
echo Instale Python 3.9 o superior desde https://www.python.org/downloads/
echo Durante la instalacion, marque "Add python.exe to PATH".
echo.
pause
exit /b 1

:python_found
echo [INFO] Python base: %BASE_PY%
echo.

if not exist "%VENV_PY%" (
    echo [INFO] Creando entorno local: App_Completa\.venv
    %BASE_PY% -m venv "%VENV_DIR%"
    if not %ERRORLEVEL%==0 (
        echo.
        echo [ERROR] No se pudo crear el entorno virtual local.
        echo Verifique que Python tenga disponible el modulo venv.
        echo.
        pause
        exit /b 1
    )
    echo.
)

"%VENV_PY%" "%PRE_APP%"
if not %ERRORLEVEL%==0 (
    echo.
    echo [ERROR] La pre-app encontro un problema. No se abrira App_Completa.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Pre-app completada. Abriendo App_Completa...
echo.

if exist "%VENV_PYW%" (
    start "" "%VENV_PYW%" "%MAIN_APP%"
) else (
    start "" "%VENV_PY%" "%MAIN_APP%"
)
exit /b 0
