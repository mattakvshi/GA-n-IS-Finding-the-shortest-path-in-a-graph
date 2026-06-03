@echo off
setlocal EnableExtensions

title AIS Shortest Path - diagnostic

echo ============================================================
echo DIAGNOSTIC
echo ============================================================
echo.
cd /d "%~dp0"

echo Current folder:
echo %CD%
echo.

echo Files in current folder:
dir
echo.

echo Checking main files:
if exist "main.py" (echo OK: main.py found) else (echo MISSING: main.py)
if exist "requirements.txt" (echo OK: requirements.txt found) else (echo MISSING: requirements.txt)
if exist "src" (echo OK: src folder found) else (echo MISSING: src folder)
if exist "results" (echo OK: results folder found) else (echo MISSING: results folder)
echo.

echo Checking Python launchers:
where py
if errorlevel 1 echo py launcher not found
where python
if errorlevel 1 echo python command not found
where python3
if errorlevel 1 echo python3 command not found
echo.

echo Version checks:
py -3 --version
python --version
python3 --version
echo.

echo If this diagnostic window opened, BAT/CMD launch works.
echo Send me a screenshot of this window if SAFE launcher does not work.
echo.
pause
exit /b 0
