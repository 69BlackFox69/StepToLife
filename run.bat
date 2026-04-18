@echo off
echo ===================================
echo StepToLife - Запуск приложения
echo ===================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не установлен или не добавлен в PATH
    pause
    exit /b 1
)

REM Создание виртуального окружения если его нет
if not exist venv (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Проверка и установка зависимостей
echo Проверка зависимостей...
pip install -r requirements.txt >nul 2>&1

REM Запуск приложения
echo.
echo Запуск Flask приложения...
echo Приложение будет доступно по адресу: http://localhost:5000
echo.
echo Нажмите Ctrl+C для остановки приложения
echo.

python app.py

pause
