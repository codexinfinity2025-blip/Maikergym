@echo off
setlocal EnableExtensions
pushd "%~dp0"
set "RAILWAY_CLI="
where railway >nul 2>nul
if not errorlevel 1 set "RAILWAY_CLI=railway"
if not defined RAILWAY_CLI if exist ".railway_npm_cache\_npx\d991ede4b4a6395c\node_modules\@railway\cli\bin\railway.exe" set "RAILWAY_CLI=%CD%\.railway_npm_cache\_npx\d991ede4b4a6395c\node_modules\@railway\cli\bin\railway.exe"
if not defined RAILWAY_CLI (
    echo ERROR: instala la CLI oficial con: npm install -g @railway/cli
    goto :fallo
)
if /i "%~1"=="--login" (
    echo Inicia sesion con la cuenta que administra MaikerGym.
    call "%RAILWAY_CLI%" login
    if errorlevel 1 goto :fallo
    popd
    exit /b 0
)
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 goto :fallo
for /f "delims=" %%B in ('git branch --show-current') do set "RAMA=%%B"
if not "%RAMA%"=="main" (
    echo ERROR: este comando publica solo desde main.
    goto :fallo
)
for /f "delims=" %%S in ('git status --porcelain') do (
    echo ERROR: hay cambios sin confirmar. Crea el commit antes de publicar.
    goto :fallo
)
for /f "delims=" %%R in ('git remote get-url --push nuevo') do set "REMOTO=%%R"
if not "%REMOTO%"=="https://github.com/codexinfinity2025-blip/Maikergym.git" (
    echo ERROR: nuevo no apunta al repositorio de MaikerGym previsto.
    goto :fallo
)
echo Comprobando acceso a GitHub...
git ls-remote --exit-code nuevo refs/heads/main
if errorlevel 1 goto :fallo
echo Comprobando acceso al proyecto Railway vinculado...
call "%RAILWAY_CLI%" status --json
if errorlevel 1 (
    echo ERROR: inicia sesion en Railway con la cuenta que administra MaikerGym.
    echo Ejecuta: .\PUBLICAR.cmd --login
    echo No se ha subido nada a GitHub ni Railway.
    goto :fallo
)
if /i "%~1"=="--comprobar" (
    echo Comprobaciones terminadas. No se ha publicado nada.
    popd
    exit /b 0
)
if not "%~1"=="" (
    echo ERROR: uso: PUBLICAR.cmd [--comprobar ^| --login]
    goto :fallo
)
echo Publicando el commit en GitHub...
git push nuevo HEAD:main
if errorlevel 1 goto :fallo
echo Solicitando despliegue en el servicio web de MaikerGym...
call "%RAILWAY_CLI%" up --project 56932f69-87d4-4401-a581-09bbb89103d4 --environment fd181040-02a8-4327-83d9-66df5286b676 --service 89d2dd62-d093-48c7-9d3f-21b51adb659f --detach
if errorlevel 1 (
    echo ERROR: GitHub fue actualizado, pero la solicitud de despliegue Railway fallo.
    echo Corrige el acceso y ejecuta este mismo comando nuevamente.
    goto :fallo
)
echo GitHub actualizado y despliegue Railway solicitado.
echo Railway sigue construyendo: revisa el estado del despliegue y /health/.
echo https://maikergym-production.up.railway.app/health/
popd
exit /b 0
:fallo
popd
exit /b 1
