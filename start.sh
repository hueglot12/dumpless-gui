#!/bin/bash

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_DIR="$ROOT_DIR"
FLUTTER_DIR="$ROOT_DIR"
VENV_DIR="$ROOT_DIR/venv"
MARYAM_DIR="$ROOT_DIR/Maryam"

if [ -d "$ROOT_DIR/flutter_app" ]; then
  FLUTTER_DIR="$ROOT_DIR/flutter_app"
fi

echo "=== Корневая папка: $ROOT_DIR ==="

check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Ошибка: команда '$1' не найдена."
    exit 1
  fi
}

echo "=== Проверка зависимостей системы ==="
check_command git
check_command python3.12

echo "=== Проверка virtualenv ==="
if [ ! -d "$VENV_DIR" ]; then
  echo "venv не найден, создаю..."
  python3.12 -m venv "$VENV_DIR"
fi

echo "=== Активация venv ==="
source "$VENV_DIR/bin/activate"

echo "=== Обновление pip ==="
python -m pip install --upgrade pip setuptools wheel

echo "=== Установка Python-зависимостей ==="
if [ -f "$ROOT_DIR/requirements.txt" ]; then
  echo "Найден requirements.txt"
  pip install -r "$ROOT_DIR/requirements.txt"
elif [ -f "$ROOT_DIR/requirements" ]; then
  echo "Найден requirements"
  pip install -r "$ROOT_DIR/requirements"
else
  echo "requirements не найден, пропускаю"
fi

echo "=== Проверка Maryam ==="
if [ ! -d "$MARYAM_DIR" ]; then
  echo "Maryam не найден, клонирую..."
  git clone https://github.com/saeeddhqan/Maryam "$MARYAM_DIR"
else
  echo "Maryam уже существует"
fi

echo "=== Установка зависимостей Maryam ==="
if [ -f "$MARYAM_DIR/requirements.txt" ]; then
  pip install -r "$MARYAM_DIR/requirements.txt" || true
elif [ -f "$MARYAM_DIR/requirements" ]; then
  pip install -r "$MARYAM_DIR/requirements" || true
else
  echo "У Maryam requirements не найден"
fi

echo "=== Освобождаю порт 5000 ==="
fuser -k 5000/tcp 2>/dev/null || true

echo "=== Запуск backend ==="
cd "$PYTHON_DIR"
python app.py &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
sleep 3

echo "=== Проверка Flutter проекта ==="
if [ ! -f "$FLUTTER_DIR/pubspec.yaml" ]; then
  echo "Ошибка: pubspec.yaml не найден."
  echo "Положи Flutter-проект либо в текущую папку, либо в ./flutter_app"
  kill "$BACKEND_PID" 2>/dev/null || true
  exit 1
fi

echo "=== Запуск Flutter ==="
cd "$FLUTTER_DIR"
flutter pub get
flutter run

echo "=== Остановка backend ==="
kill "$BACKEND_PID" 2>/dev/null || true