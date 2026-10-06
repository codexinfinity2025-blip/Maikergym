@echo off
REM Cambia al directorio del proyecto
cd /d "%~dp0"

REM Detecta si hay python o py disponible
set PY_EXEC=
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 set PY_EXEC=python
if not defined PY_EXEC (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 set PY_EXEC=py
)
if not defined PY_EXEC (
    set "PY_PATH=C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\python.exe"
    if exist "%PY_PATH%" set PY_EXEC="%PY_PATH%"
)
if not defined PY_EXEC (
    echo ERROR: no se encontro Python en PATH.
    echo Instala Python 3.12 y marca "Add Python to PATH".
    pause
    exit /b 1
)

echo Usando interprete: %PY_EXEC%

REM Copia el archivo de ejemplo .env si no existe
if not exist .env (
    copy .env.example .env
)

REM Instala dependencias
%PY_EXEC% -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: no se pudo instalar las dependencias.
    echo Asegurate de tener Python instalado y que pip funcione.
    pause
    exit /b 1
)

REM Crea la base de datos MySQL si no existe
%PY_EXEC% create_mysql_db.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: no se pudo crear o conectar a la base de datos MySQL.
    echo Revisa que MySQL este corriendo y que los datos en .env sean correctos.
    pause
    exit /b 1
)

REM Aplica migraciones a la base de datos
%PY_EXEC% manage.py migrate
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: no se pudo aplicar migrate.
    pause
    exit /b 1
)

REM Crea datos de prueba
%PY_EXEC% setup.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: no se pudieron crear los usuarios de prueba.
    pause
    exit /b 1
)

REM Inicia el servidor local
%PY_EXEC% manage.py runserver
