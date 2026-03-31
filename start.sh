#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_DIR="$ROOT_DIR"
FLUTTER_DIR="$ROOT_DIR"
VENV_DIR="$ROOT_DIR/venv"

MAILCAT_DIR="$ROOT_DIR/mailcat"
BLACKBIRD_DIR="$ROOT_DIR/blackbird"

MAILCAT_REPO="https://github.com/sharsil/mailcat.git"
BLACKBIRD_REPO="https://github.com/worldofcyberskills/Blackbird.git"

if [ -d "$ROOT_DIR/flutter_app" ]; then
  FLUTTER_DIR="$ROOT_DIR/flutter_app"
fi

BACKEND_PID=""

cleanup() {
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

log() {
  echo
  echo "=== $1 ==="
}

check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Ошибка: команда '$1' не найдена."
    exit 1
  fi
}

detect_pkg_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "apt"
    return
  fi
  if command -v dnf >/dev/null 2>&1; then
    echo "dnf"
    return
  fi
  if command -v pacman >/dev/null 2>&1; then
    echo "pacman"
    return
  fi
  if command -v pkg >/dev/null 2>&1; then
    echo "pkg"
    return
  fi
  echo "unknown"
}

install_system_deps() {
  local pm="$1"

  case "$pm" in
    apt)
      sudo apt-get update
      sudo apt-get install -y \
        git curl wget unzip xdg-utils \
        python3 python3-venv python3-pip \
        build-essential libffi-dev libssl-dev \
        rustc cargo \
        flutter
      ;;
    dnf)
      sudo dnf install -y \
        git curl wget unzip xdg-utils \
        python3 python3-virtualenv python3-pip \
        gcc gcc-c++ make redhat-rpm-config \
        libffi-devel openssl-devel \
        rust cargo \
        flutter
      ;;
    pacman)
      sudo pacman -Sy --noconfirm \
        git curl wget unzip xdg-utils \
        python python-pip base-devel \
        libffi openssl \
        rust cargo \
        flutter
      ;;
    pkg)
      pkg update -y
      pkg install -y \
        git curl wget unzip x11-repo \
        python clang make \
        rust
      ;;
    *)
      echo "Не удалось определить менеджер пакетов."
      echo "Установи вручную: git, python3, pip, venv, rust, cargo, flutter"
      exit 1
      ;;
  esac
}

ensure_repo() {
  local repo_url="$1"
  local target_dir="$2"

  if [ ! -d "$target_dir/.git" ]; then
    git clone "$repo_url" "$target_dir"
  else
    git -C "$target_dir" pull --ff-only || true
  fi
}

install_python_reqs_if_exists() {
  local target_dir="$1"

  if [ -f "$target_dir/requirements.txt" ]; then
    pip install -r "$target_dir/requirements.txt"
  elif [ -f "$target_dir/requirements" ]; then
    pip install -r "$target_dir/requirements"
  fi
}

log "Корневая папка: $ROOT_DIR"

log "Проверка базовых зависимостей"
check_command git
check_command python3 || check_command python

PKG_MANAGER="$(detect_pkg_manager)"
log "Менеджер пакетов: $PKG_MANAGER"

log "Установка системных зависимостей"
install_system_deps "$PKG_MANAGER"

log "Создание virtualenv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR" 2>/dev/null || python -m venv "$VENV_DIR"
fi

log "Активация venv"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

log "Обновление pip"
python -m pip install --upgrade pip setuptools wheel

log "Установка Python-зависимостей проекта"
if [ -f "$ROOT_DIR/requirements.txt" ]; then
  pip install -r "$ROOT_DIR/requirements.txt"
elif [ -f "$ROOT_DIR/requirements" ]; then
  pip install -r "$ROOT_DIR/requirements"
else
  echo "requirements не найден, пропускаю"
fi

log "Установка holehe"
pip install --upgrade holehe

log "Клонирование и обновление Mailcat"
ensure_repo "$MAILCAT_REPO" "$MAILCAT_DIR"

log "Установка зависимостей Mailcat"
install_python_reqs_if_exists "$MAILCAT_DIR"
if [ -f "$MAILCAT_DIR/setup.py" ]; then
  pip install -e "$MAILCAT_DIR" || true
fi

log "Клонирование и обновление Blackbird"
ensure_repo "$BLACKBIRD_REPO" "$BLACKBIRD_DIR"

log "Установка зависимостей Blackbird"
install_python_reqs_if_exists "$BLACKBIRD_DIR"
if [ -f "$BLACKBIRD_DIR/setup.py" ]; then
  pip install -e "$BLACKBIRD_DIR" || true
fi

log "Проверка holehe"
holehe --help >/dev/null 2>&1 || {
  echo "holehe не запускается"
  exit 1
}

log "Освобождаю порт 5000"
if command -v fuser >/dev/null 2>&1; then
  fuser -k 5000/tcp 2>/dev/null || true
elif command -v lsof >/dev/null 2>&1; then
  lsof -ti:5000 | xargs -r kill -9 || true
fi

log "Запуск backend"
cd "$PYTHON_DIR"
python app.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

sleep 3

log "Проверка Flutter проекта"
if [ ! -f "$FLUTTER_DIR/pubspec.yaml" ]; then
  echo "Ошибка: pubspec.yaml не найден."
  echo "Положи Flutter-проект либо в текущую папку, либо в ./flutter_app"
  exit 1
fi

log "Flutter pub get"
cd "$FLUTTER_DIR"
flutter pub get

log "Запуск Flutter"
flutter run