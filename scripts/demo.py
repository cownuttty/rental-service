"""Демонстрационный сценарий: создаёт данные через REST API и печатает ответы.

Запуск (приложение должно быть запущено):
    python scripts/demo.py                       # http://localhost:5000
    python scripts/demo.py --url http://localhost:5000
"""
import argparse
import json
import time
import urllib.error
import urllib.request


def call(base_url, method, path, payload=None):
    """Отправляет HTTP-запрос и возвращает (код ответа, JSON)."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        base_url + path, data=body, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, json.loads(raw) if raw else None


def show(title, result):
    status, data = result
    print(f"\n### {title}\nHTTP {status}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def main():
    parser = argparse.ArgumentParser(description="Демо-сценарий аренды квартиры")
    parser.add_argument("--url", default="http://localhost:5000")
    url = parser.parse_args().url.rstrip("/")
    stamp = int(time.time())  # делает e-mail уникальными при повторном запуске

    owner = show("1. Собственник", call(url, "POST", "/owners", {
        "full_name": "Иван Петров", "phone": "+7 900 111-22-33",
        "email": f"owner{stamp}@example.com", "commission_percent": 20}))
    apartment = show("2. Квартира собственника", call(url, "POST", "/apartments", {
        "owner_id": owner["id"], "title": "Студия у метро", "address": "Москва, ул. Ленина, 1",
        "rooms": 1, "capacity": 2, "price_per_night": 3000}))
    guest = show("3. Клиент", call(url, "POST", "/clients", {
        "full_name": "Анна Смирнова", "phone": "+7 900 555-66-77",
        "email": f"client{stamp}@example.com"}))
    cleaner = show("4. Горничная", call(url, "POST", "/cleaners", {
        "full_name": "Мария Иванова", "phone": "+7 900 000-11-22"}))

    show("5. Свободна ли квартира на 1-5 октября 2026?", call(
        url, "GET", f"/apartments/{apartment['id']}/availability"
        "?check_in=2026-10-01&check_out=2026-10-05"))
    booking = show("6. Бронирование (стоимость считает сервер)", call(url, "POST", "/bookings", {
        "apartment_id": apartment["id"], "client_id": guest["id"],
        "check_in": "2026-10-01", "check_out": "2026-10-05", "guests": 2}))
    show("7. Повторная бронь на пересекающиеся даты -> 409", call(url, "POST", "/bookings", {
        "apartment_id": apartment["id"], "client_id": guest["id"],
        "check_in": "2026-10-03", "check_out": "2026-10-06"}))
    show("8. Подтверждение брони", call(
        url, "PUT", f"/bookings/{booking['id']}", {"status": "confirmed"}))
    show("9. Отчёт собственнику (доход, комиссия УК, выплата)", call(
        url, "GET", f"/owners/{owner['id']}/report"))
    show("10. Гость выехал: бронь завершена", call(
        url, "PUT", f"/bookings/{booking['id']}", {"status": "completed"}))

    status, tasks = call(url, "GET", "/cleaning-tasks")
    if status == 200:
        show("11. Задачи на уборку (создались автоматически)", (status, tasks))
        if tasks:
            show("12. Назначаем горничную", call(
                url, "PUT", f"/cleaning-tasks/{tasks[-1]['id']}",
                {"cleaner_id": cleaner["id"], "cost": 1500}))
    else:
        print("\n(Задачи на уборку появятся в версии с фичей feature/cleaning-tasks)")


if __name__ == "__main__":
    main()
