@echo off
setlocal

title Revise - Update and Start
cd /d "C:\Users\jatin\OneDrive\Desktop\Projects\Revise"

set "ROOT=%CD%"
set "WEB=%ROOT%\web"
set "ENV_BACKUP=%TEMP%\Revise_env_backup"

if not exist "%WEB%" (
    echo [ERROR] Web directory not found: "%WEB%"
    pause
    exit /b 1
)

echo.
echo ==========================================
echo       REVISE - UPDATE AND START
echo ==========================================
echo.

echo [1/6] Checking repository...
git rev-parse --show-toplevel >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This is not a Git repository: "%ROOT%"
    pause
    exit /b 1
)

echo [2/6] Saving local .env...
if exist ".env" copy /Y ".env" "%ENV_BACKUP%" >nul

echo [3/6] Fetching latest main...
git fetch origin main
if errorlevel 1 (
    echo [ERROR] Failed to fetch origin/main.
    goto :fail
)

echo [4/6] Forcing local main to exact origin/main...
git checkout -B main origin/main
if errorlevel 1 (
    echo [ERROR] Failed to align local main with origin/main.
    goto :fail
)

git reset --hard origin/main
if errorlevel 1 (
    echo [ERROR] Failed to reset local main to origin/main.
    goto :fail
)

echo [5/6] Restoring local .env...
if exist "%ENV_BACKUP%" (
    copy /Y "%ENV_BACKUP%" ".env" >nul
    del /Q "%ENV_BACKUP%" >nul 2>&1
)

echo.
echo Verifying exact main state...
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main

git merge-base --is-ancestor HEAD origin/main
if errorlevel 1 (
    echo [ERROR] Local main is not aligned with origin/main.
    goto :fail_no_env
)
git diff --quiet HEAD origin/main
if errorlevel 1 (
    echo [ERROR] Local main differs from origin/main.
    goto :fail_no_env
)

echo [6/6] Starting engine and web server...
start "Revise Engine" cmd /k "cd /d %ROOT% && python -m engine --serve"

timeout /t 2 /nobreak >nul

start "Revise Web" cmd /k "cd /d %WEB% && npm run dev"

echo.
echo ==========================================
echo Engine: http://127.0.0.1:8000
echo Web:    http://localhost:3000
echo ==========================================
echo.
exit /b 0

:fail
if exist "%ENV_BACKUP%" (
    copy /Y "%ENV_BACKUP%" ".env" >nul
    del /Q "%ENV_BACKUP%" >nul 2>&1
)
:fail_no_env
echo.
echo [ERROR] Revise startup aborted.
pause
exit /b 1
