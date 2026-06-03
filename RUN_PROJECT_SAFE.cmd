@echo off
setlocal EnableExtensions

title AIS Shortest Path - SAFE launcher

echo ============================================================
echo AIS Shortest Path project - SAFE launcher
echo ============================================================
echo.
echo This window must stay open.
echo If you see this text, CMD files are working on this computer.
echo.
cd /d "%~dp0"

echo Current folder:
echo %CD%
echo.

if not exist "main.py" (
    echo ERROR: main.py was not found in this folder.
    echo You probably started the script from inside WinRAR.
    echo Please extract the whole archive first, then run this file.
    echo.
    pause
    exit /b 1
)

if not exist "src" (
    echo ERROR: src folder was not found.
    echo Please extract the whole archive first.
    echo.
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
    echo.
    echo Install Python 3.11+ from python.org
    echo IMPORTANT: enable "Add Python to PATH" during installation.
    echo.
    echo After installation close this window and run this file again.
    echo.
    pause
    exit /b 1
)

echo Python command:
echo %PY%
%PY% --version
echo.

echo Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo Creating .venv...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo ERROR: failed to create virtual environment.
        echo Try to run this file from a folder with normal write permissions.
        echo.
        pause
        exit /b 1
    )
) else (
    echo .venv already exists.
)
echo.

echo Installing dependencies...
".venv\Scripts\python.exe" -m ensurepip --upgrade >nul 2>nul
".venv\Scripts\python.exe" -m pip install --upgrade pip

if exist "requirements.txt" (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
    ".venv\Scripts\python.exe" -m pip install networkx matplotlib
)

if errorlevel 1 (
    echo.
    echo ERROR: dependencies were not installed.
    echo Check internet connection.
    echo.
    pause
    exit /b 1
)

echo.
echo Running main.py...
".venv\Scripts\python.exe" main.py

if errorlevel 1 (
    echo.
    echo ERROR: main.py failed.
    echo.
    pause
    exit /b 1
)

echo.
echo Demo completed.
echo Results are in the results folder.
echo.

choice /C YN /M "Run experiments too"
if errorlevel 2 goto finish

echo.
echo Running experiments...
".venv\Scripts\python.exe" -m src.experiments

if errorlevel 1 (
    echo.
    echo ERROR: experiments failed.
    echo.
    pause
    exit /b 1
)

:finish
echo.
echo ============================================================
echo DONE
echo ============================================================
echo.
pause
exit /b 0
