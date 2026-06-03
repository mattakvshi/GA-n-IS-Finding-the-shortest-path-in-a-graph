@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title Sidorenko IS Shortest Path - auto run

echo ============================================================
echo  Искусственная иммунная сеть: поиск кратчайшего пути в графе
echo  Автоматическая проверка окружения и запуск проекта
echo ============================================================
echo.

cd /d "%~dp0"

set "PY_CMD="
set "VENV_DIR=.venv"
set "REQ_FILE=requirements.txt"
set "LOG_DIR=results"
set "LOG_FILE=%LOG_DIR%\run_project_bat_log.txt"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo [%date% %time%] Запуск run_project.bat > "%LOG_FILE%"

echo [1/5] Проверка Python...
call :find_python

if not defined PY_CMD (
    echo Python не найден.
    echo [%date% %time%] Python не найден >> "%LOG_FILE%"
    echo.
    echo Попытка установить Python 3.11 через winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo.
        echo winget не найден. Автоматически установить Python не удалось.
        echo Установите Python вручную с сайта python.org, отметьте галочку "Add Python to PATH",
        echo затем снова запустите этот файл.
        echo.
        pause
        exit /b 1
    )

    winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements

    echo.
    echo Повторная проверка Python после установки...
    call :find_python

    if not defined PY_CMD (
        echo.
        echo Python установлен, но текущая консоль пока не видит его в PATH.
        echo Закройте это окно и запустите run_project.bat ещё раз.
        echo.
        pause
        exit /b 1
    )
)

echo Python найден: %PY_CMD%
%PY_CMD% --version
echo [%date% %time%] Python: %PY_CMD% >> "%LOG_FILE%"
%PY_CMD% --version >> "%LOG_FILE%" 2>&1
echo.

echo [2/5] Проверка виртуального окружения...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Виртуальное окружение не найдено. Создаю %VENV_DIR%...
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Не удалось создать виртуальное окружение.
        echo Проверьте установку Python и права доступа к папке проекта.
        pause
        exit /b 1
    )
) else (
    echo Виртуальное окружение уже существует.
)
echo [%date% %time%] venv OK >> "%LOG_FILE%"
echo.

set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

echo [3/5] Проверка pip и установка библиотек...
"%VENV_PY%" -m ensurepip --upgrade >nul 2>nul
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 (
    echo Не удалось обновить pip. Продолжаю попытку установки зависимостей...
)

if exist "%REQ_FILE%" (
    echo Устанавливаю зависимости из %REQ_FILE%...
    "%VENV_PY%" -m pip install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo.
        echo Не удалось установить зависимости.
        echo Проверьте интернет-соединение и файл requirements.txt.
        echo.
        pause
        exit /b 1
    )
) else (
    echo Файл requirements.txt не найден.
    echo Устанавливаю минимальный набор библиотек: networkx matplotlib.
    "%VENV_PY%" -m pip install networkx matplotlib
    if errorlevel 1 (
        echo Не удалось установить библиотеки.
        pause
        exit /b 1
    )
)
echo [%date% %time%] dependencies OK >> "%LOG_FILE%"
echo.

echo [4/5] Запуск демонстрации main.py...
"%VENV_PY%" main.py
if errorlevel 1 (
    echo.
    echo Ошибка при запуске main.py.
    echo Подробности выше в окне консоли.
    echo.
    pause
    exit /b 1
)
echo [%date% %time%] main.py OK >> "%LOG_FILE%"
echo.

echo [5/5] Хотите запустить экспериментальную серию и построить графики?
echo Это создаст/обновит results\experiment_results.csv и графики.
choice /C YN /M "Запустить эксперименты"
if errorlevel 2 goto skip_experiments

echo.
echo Запускаю эксперименты...
"%VENV_PY%" -m src.experiments
if errorlevel 1 (
    echo.
    echo Ошибка при запуске экспериментов.
    echo Демонстрационный запуск уже выполнен, но эксперименты не завершились.
    echo.
    pause
    exit /b 1
)
echo [%date% %time%] experiments OK >> "%LOG_FILE%"

:skip_experiments
echo.
echo ============================================================
echo  Готово.
echo ============================================================
echo.
echo Основные результаты находятся в папке results:
echo  - path_visualization.png
echo  - objective_vs_iterations_demo.png
echo  - demo_summary.json
echo  - experiment_results.csv
echo  - time_vs_graph_size.png
echo  - objective_vs_iterations.png
echo.
echo Для отчёта см. папку report.
echo.
pause
exit /b 0


:find_python
set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=py -3"
        exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    python --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python"
        exit /b 0
    )
)

where python3 >nul 2>nul
if not errorlevel 1 (
    python3 --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python3"
        exit /b 0
    )
)

exit /b 0
