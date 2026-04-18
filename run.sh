#!/bin/bash

echo "==================================="
echo "StepToLife - Запуск приложения"
echo "==================================="
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python 3 не установлен"
    exit 1
fi

# Создание виртуального окружения если его нет
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Проверка и установка зависимостей
echo "Проверка зависимостей..."
pip install -r requirements.txt > /dev/null 2>&1

# Запуск приложения
echo ""
echo "Запуск Flask приложения..."
echo "Приложение будет доступно по адресу: http://localhost:5000"
echo ""
echo "Нажмите Ctrl+C для остановки приложения"
echo ""

python app.py
