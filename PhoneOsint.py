import re
import subprocess
import html
import sys
import os
import platform
from deep_translator import GoogleTranslator

PYTHON_BIN = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MARYAM_PATH = os.path.join(BASE_DIR, "Maryam", "maryam.py")


def normalize_phone(num: str) -> str:
    # просто оставляем цифры
    return re.sub(r"\D+", "", num)

def tr(text: str) -> str:
    if not text or text.lower() in ("unknown", "not found"):
        return "не найдено"

    try:
        return GoogleTranslator(source="auto", target="ru").translate(text)
    except Exception:
        return text


def parse_maryam_output(output: str) -> dict:
    wanted_keys = {
        "VALID": "не найдено",
        "COUNTRY CODE": "не найдено",
        "COUNTRY NAME": "не найдено",
        "LOCATION": "не найдено",
        "CARRIER": "не найдено",
        "LINE TYPE": "не найдено",
    }

    output = re.sub(r"\x1b\[[0-9;]*m", "", output)  # remove colors

    lines = [line.strip() for line in output.splitlines() if line.strip()]
    current_key = None

    for line in lines:
        if line.startswith("[*]"):
            line = line[3:].strip()

        if line in wanted_keys:
            current_key = line
            continue

        if current_key:
            wanted_keys[current_key] = line
            current_key = None

    return wanted_keys


async def phone_search(phone_number: str):
    phone = normalize_phone(phone_number)

    if len(phone) < 7:
        return "❌ Некорректный номер"

    if not os.path.exists(MARYAM_PATH):
        return "❌ Maryam не найден"

    # --- Windows: запускаем через WSL ---
    if platform.system().lower() == "windows":
        # Пример пути в WSL: /mnt/c/Users/User/Documents/bear-search2/Maryam/maryam.py
        wsl_path = MARYAM_PATH.replace("\\", "/").replace("C:", "/mnt/c")

        cmd = [
            "wsl",
            "python3",
            wsl_path,
            "-e",
            "phone_number_search",
            "-n",
            phone
        ]
    else:
        cmd = [PYTHON_BIN, MARYAM_PATH, "-e", "phone_number_search", "-n", phone]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=25
    )

    raw_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    data = parse_maryam_output(raw_output)

    return (
        "📞 Результаты По Номеру:\n"
        f"├ Номер: {phone}\n"
        f"├ Валидный: {tr(data['VALID'])}\n"
        f"├ Страна: {tr(data['COUNTRY NAME'])} ({data['COUNTRY CODE']})\n"
        f"├ Регион: {tr(data['LOCATION'])}\n"
        f"├ Оператор: {tr(data['CARRIER'])}\n"
        f"└ Тип линии: {tr(data['LINE TYPE'])}"
        )

