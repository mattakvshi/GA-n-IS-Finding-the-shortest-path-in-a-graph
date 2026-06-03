@echo off
setlocal EnableExtensions

title AIS Shortest Path - WEB GUI

echo ============================================================
echo AIS Shortest Path - WEB GUI launcher
echo ============================================================
echo.
cd /d "%~dp0"

if not exist "web_app.py" (
    echo ERROR: web_app.py was not found.
    echo Run this file from the project folder.
    pause
    exit /b 1
)

set "PY="
where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 set "PY=py -3"
)

if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 (
        python --version >nul 2>nul
        if not errorlevel 1 set "PY=python"
    )
)

if not defined PY (
    echo Python was not found.
    echo Install Python 3.11+ from python.org and enable "Add Python to PATH".
    pause
    exit /b 1
)

echo Python command: %PY%
%PY% --version
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo ERROR: failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing/updating dependencies...
".venv\Scripts\python.exe" -m ensurepip --upgrade >nul 2>nul
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: dependencies were not installed.
    pause
    exit /b 1
)

echo.
echo Starting web interface...
echo Browser should open automatically.
echo If not, open this address manually:
echo http://127.0.0.1:5000
echo.
echo Keep this window open while using the GUI.
echo Press Ctrl+C to stop the server.
echo.

".venv\Scripts\python.exe" web_app.py

pause
exit /b 0
