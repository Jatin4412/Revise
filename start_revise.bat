@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Revise - Launcher

set "ROOT=C:\Users\jatin\OneDrive\Desktop\Projects\Revise"
set "WEB=%ROOT%\web"
set "ENV_BACKUP=%TEMP%\Revise_env_backup_%RANDOM%.env"

cd /d "%ROOT%"

if not exist "%ROOT%\.git" (
    echo [ERROR] Git repository not found.
    pause
    exit /b 1
)

:menu
cls
echo.
echo ============================
echo        REVISE
echo ============================
echo.
echo Available branches:
echo.

git fetch --prune origin >nul 2>&1
set "COUNT=0"

for /f "delims=" %%B in ('git branch -r --format="%%(refname:short)" ^| findstr /v /r "^origin/HEAD"') do (
    set /a COUNT+=1
    set "BRANCH[!COUNT!]=%%B"
    echo !COUNT!^) %%B
)

echo.
echo X^) Exit
echo.
set /p "CHOICE=Select branch: "

if /i "%CHOICE%"=="X" goto :close
if not defined BRANCH[%CHOICE%] (
    echo.
    echo Invalid selection.
    timeout /t 2 >nul
    goto :menu
)

set "SELECTED=!BRANCH[%CHOICE%]!"
set "SELECTED=!SELECTED:origin/=!"

echo.
echo Updating %SELECTED%...

if exist "%ROOT%\.env" copy /Y "%ROOT%\.env" "%ENV_BACKUP%" >nul

git reset --hard
if errorlevel 1 goto :git_error

git checkout -B "%SELECTED%" "origin/%SELECTED%"
if errorlevel 1 goto :git_error

git reset --hard "origin/%SELECTED%"
if errorlevel 1 goto :git_error

if exist "%ENV_BACKUP%" (
    copy /Y "%ENV_BACKUP%" "%ROOT%\.env" >nul
    del /Q "%ENV_BACKUP%"
)

:ready
cls
echo.
echo ============================
echo      REVISE - %SELECTED%
echo ============================
echo.
echo R^) Run engine + browser UI
echo T^) Run all engine tests
echo X^) Exit
echo.
choice /c RTX /n /m "Select: "

if errorlevel 3 goto :close
if errorlevel 2 goto :tests
if errorlevel 1 goto :run

:tests
cls
echo.
echo ============================
echo       ENGINE TESTS
echo ============================
echo.
python -m unittest discover -s engine -t . -p "test*.py" -v
set "TEST_RESULT=%ERRORLEVEL%"
echo.
if "%TEST_RESULT%"=="0" (
    echo [OK] All engine tests passed.
) else (
    echo [FAIL] Engine tests failed. See output above.
)
echo.
pause
goto :ready

:run
cls
echo.
echo ============================
echo       REVISE RUNNING
echo ============================
echo.
echo Branch: %SELECTED%
echo.
echo Starting engine console...
start "Revise Engine" /D "%ROOT%" cmd /k python -m engine --serve

timeout /t 2 /nobreak >nul

echo Starting browser UI console...
start "Revise Web" /D "%WEB%" cmd /k npm run dev

echo.
echo Engine: http://127.0.0.1:8000
echo Web:    http://localhost:3000
echo.
echo R = stop both + choose branch again
echo X = stop both + exit launcher
echo.

:running
choice /c RX /n /m "R=Restart  X=Close: "
if errorlevel 2 goto :close
if errorlevel 1 goto :restart

:restart
call :stop
goto :menu

:close
call :stop
echo.
echo Revise closed.
exit /b 0

:stop
taskkill /FI "WINDOWTITLE eq Revise Engine*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Revise Web*" /T /F >nul 2>&1
exit /b 0

:git_error
echo.
echo [ERROR] Failed to update branch.
if exist "%ENV_BACKUP%" (
    copy /Y "%ENV_BACKUP%" "%ROOT%\.env" >nul
    del /Q "%ENV_BACKUP%"
)
pause
goto :menu
