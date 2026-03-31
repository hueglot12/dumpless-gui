import re
import requests


def normalize_bin(card_or_bin: str) -> str:
    digits = re.sub(r"\D+", "", card_or_bin or "")
    return digits[:6]


def bin_info(card_or_bin: str):
    bin_number = normalize_bin(card_or_bin)

    if len(bin_number) < 6:
        return "❌ Нужно минимум 6 цифр BIN или номер карты"

    response = requests.get(
        f"https://lookup.binlist.net/{bin_number}",
        timeout=10,
        headers={"Accept-Version": "3"},
    )

    if response.status_code == 200:
        info = response.json()
        return (
            "🏦 Информация по Карте:\n"
            f"├ BIN: {bin_number}\n"
            f"├ Бренд: {info.get('brand', 'Неизвестно')}\n"
            f"├ Тип карты: {info.get('type', 'Неизвестно')}\n"
            f"├ Уровень: {info.get('level', 'Неизвестно')}\n"
            f"├ Эмитент: {info.get('bank', {}).get('name', 'Неизвестно')}\n"
            f"└ Страна: {info.get('country', {}).get('name', 'Неизвестно')}"
        )

    if response.status_code == 404:
        return "Информация не найдена."

    return f"Ошибка BIN lookup: {response.status_code}"


__add__ = ['bin_info']