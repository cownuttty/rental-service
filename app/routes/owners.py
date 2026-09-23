"""Собственники квартир: CRUD + отчёт о доходе."""
import sqlite3

from flask import Blueprint, jsonify

from ..db import delete_row, get_db, get_row, insert_row, update_row
from ..utils import blank_fields, error, get_json_object, is_number, missing_fields

bp = Blueprint("owners", __name__, url_prefix="/owners")

FIELDS = ("full_name", "phone", "email", "commission_percent")
REQUIRED = ("full_name", "phone", "email")


def validate(data, partial):
    """Возвращает текст ошибки или None. partial=True — для обновления (PUT)."""
    if not partial:
        missing = missing_fields(data, REQUIRED)
        if missing:
            return "missing required fields: " + ", ".join(missing)
    blank = blank_fields(data, REQUIRED)
    if blank:
        return "fields must not be empty: " + ", ".join(blank)
    if "email" in data and "@" not in str(data["email"]):
        return "email is invalid"
    if "commission_percent" in data and not is_number(data["commission_percent"], 0, 100):
        return "commission_percent must be a number between 0 and 100"
    return None


@bp.post("")
def create_owner():
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=False)
    if problem:
        return error(problem)
    values = {name: data[name] for name in FIELDS if name in data}
    try:
        owner_id = insert_row("owners", values)
    except sqlite3.IntegrityError:
        return error("owner with this email already exists", 409)
    return jsonify(dict(get_row("owners", owner_id))), 201


@bp.get("")
def list_owners():
    rows = get_db().execute("SELECT * FROM owners ORDER BY id").fetchall()
    return jsonify([dict(row) for row in rows])


@bp.get("/<int:owner_id>")
def get_owner(owner_id):
    row = get_row("owners", owner_id)
    if row is None:
        return error("owner not found", 404)
    return jsonify(dict(row))


@bp.put("/<int:owner_id>")
def update_owner(owner_id):
    if get_row("owners", owner_id) is None:
        return error("owner not found", 404)
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=True)
    if problem:
        return error(problem)
    values = {name: data[name] for name in FIELDS if name in data}
    try:
        update_row("owners", owner_id, values)
    except sqlite3.IntegrityError:
        return error("owner with this email already exists", 409)
    return jsonify(dict(get_row("owners", owner_id)))


@bp.delete("/<int:owner_id>")
def delete_owner(owner_id):
    if get_row("owners", owner_id) is None:
        return error("owner not found", 404)
    try:
        delete_row("owners", owner_id)
    except sqlite3.IntegrityError:
        return error("owner has apartments and cannot be deleted", 409)
    return "", 204


@bp.get("/<int:owner_id>/report")
def owner_report(owner_id):
    """Сколько заработали квартиры собственника и сколько ему выплатить.

    В доход входят подтверждённые и завершённые бронирования.
    Комиссия управляющей компании = доход * commission_percent / 100.
    """
    owner = get_row("owners", owner_id)
    if owner is None:
        return error("owner not found", 404)
    row = get_db().execute(
        "SELECT COUNT(b.id) AS bookings_count, COALESCE(SUM(b.total_price), 0) AS income "
        "FROM bookings b JOIN apartments a ON a.id = b.apartment_id "
        "WHERE a.owner_id = ? AND b.status IN ('confirmed', 'completed')",
        (owner_id,),
    ).fetchone()
    income = round(row["income"], 2)
    commission = round(income * owner["commission_percent"] / 100, 2)
    return jsonify(
        {
            "owner_id": owner_id,
            "bookings_count": row["bookings_count"],
            "income": income,
            "commission": commission,
            "payout": round(income - commission, 2),
        }
    )
