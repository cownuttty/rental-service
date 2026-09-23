"""Общие функции: формат ошибок и проверка входных данных."""
from datetime import date

from flask import jsonify, request


def error(message, status=400):
    """Единый формат ответа с ошибкой: {"error": "..."}."""
    return jsonify({"error": message}), status


def get_json_object():
    """Тело запроса как dict или None, если пришёл не JSON-объект."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def missing_fields(data, names):
    """Обязательные поля, которых нет или которые пустые."""
    return [n for n in names if data.get(n) is None or str(data[n]).strip() == ""]


def blank_fields(data, names):
    """Поля, которые переданы, но пустые (для частичного обновления)."""
    return [n for n in names if n in data and (data[n] is None or str(data[n]).strip() == "")]


def is_number(value, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if minimum is not None and value < minimum:
        return False
    return maximum is None or value <= maximum


def is_int(value, minimum=None):
    return isinstance(value, int) and not isinstance(value, bool) and is_number(value, minimum)


def parse_date(value):
    """'2026-10-01' -> date, всё остальное -> None."""
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
