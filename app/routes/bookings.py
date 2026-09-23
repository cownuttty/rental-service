"""Бронирования: CRUD + бизнес-правила (пересечение дат, вместимость, расчёт стоимости)."""
from flask import Blueprint, jsonify, request

from ..db import delete_row, get_db, get_row, insert_row, update_row
from ..services import find_conflict
from ..utils import error, get_json_object, is_int, missing_fields, parse_date

bp = Blueprint("bookings", __name__, url_prefix="/bookings")

STATUSES = ("new", "confirmed", "cancelled", "completed")
REQUIRED = ("apartment_id", "client_id", "check_in", "check_out")


def check_booking(apartment, check_in, check_out, guests, exclude_id=None):
    """Проверяет даты, число гостей и занятость квартиры.

    Возвращает (текст ошибки, HTTP-код) или None, если всё в порядке.
    """
    start, end = parse_date(check_in), parse_date(check_out)
    if start is None or end is None:
        return "check_in and check_out must be dates in YYYY-MM-DD format", 400
    if end <= start:
        return "check_out must be later than check_in", 400
    if not is_int(guests, 1):
        return "guests must be an integer >= 1", 400
    if guests > apartment["capacity"]:
        return "number of guests exceeds apartment capacity", 400
    if find_conflict(apartment["id"], start.isoformat(), end.isoformat(), exclude_id):
        return "apartment is already booked for these dates", 409
    return None


def calc_total(apartment, check_in, check_out):
    """Стоимость = число ночей * цена за ночь."""
    nights = (parse_date(check_out) - parse_date(check_in)).days
    return round(nights * apartment["price_per_night"], 2)


@bp.post("")
def create_booking():
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    missing = missing_fields(data, REQUIRED)
    if missing:
        return error("missing required fields: " + ", ".join(missing))

    apartment = get_row("apartments", data["apartment_id"])
    if apartment is None:
        return error("apartment not found")
    if get_row("clients", data["client_id"]) is None:
        return error("client not found")
    if apartment["status"] != "active":
        return error("apartment is not available for booking", 409)

    guests = data.get("guests", 1)
    problem = check_booking(apartment, data["check_in"], data["check_out"], guests)
    if problem:
        return error(*problem)

    booking_id = insert_row(
        "bookings",
        {
            "apartment_id": apartment["id"],
            "client_id": data["client_id"],
            "check_in": data["check_in"],
            "check_out": data["check_out"],
            "guests": guests,
            "total_price": calc_total(apartment, data["check_in"], data["check_out"]),
        },
    )
    return jsonify(dict(get_row("bookings", booking_id))), 201


@bp.get("")
def list_bookings():
    """Фильтры (необязательные): ?apartment_id=1&client_id=2&status=new"""
    clauses, params = [], []
    for name in ("apartment_id", "client_id", "status"):
        if name in request.args:
            clauses.append(f"{name} = ?")
            params.append(request.args[name])
    query = "SELECT * FROM bookings"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    rows = get_db().execute(query + " ORDER BY id", params).fetchall()
    return jsonify([dict(row) for row in rows])


@bp.get("/<int:booking_id>")
def get_booking(booking_id):
    row = get_row("bookings", booking_id)
    if row is None:
        return error("booking not found", 404)
    return jsonify(dict(row))


@bp.put("/<int:booking_id>")
def update_booking(booking_id):
    """Можно менять статус, даты и число гостей. Квартиру и клиента менять нельзя."""
    booking = get_row("bookings", booking_id)
    if booking is None:
        return error("booking not found", 404)
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    if "status" in data and data["status"] not in STATUSES:
        return error("status must be one of: " + ", ".join(STATUSES))

    values = {n: data[n] for n in ("check_in", "check_out", "guests", "status") if n in data}
    if any(name in values for name in ("check_in", "check_out", "guests")):
        apartment = get_row("apartments", booking["apartment_id"])
        check_in = values.get("check_in", booking["check_in"])
        check_out = values.get("check_out", booking["check_out"])
        guests = values.get("guests", booking["guests"])
        problem = check_booking(apartment, check_in, check_out, guests, exclude_id=booking_id)
        if problem:
            return error(*problem)
        values["total_price"] = calc_total(apartment, check_in, check_out)

    update_row("bookings", booking_id, values)
    return jsonify(dict(get_row("bookings", booking_id)))


@bp.delete("/<int:booking_id>")
def delete_booking(booking_id):
    if get_row("bookings", booking_id) is None:
        return error("booking not found", 404)
    delete_row("bookings", booking_id)
    return "", 204
