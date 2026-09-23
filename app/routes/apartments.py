"""Квартиры: CRUD + проверка доступности на даты."""
import sqlite3

from flask import Blueprint, jsonify, request

from ..db import delete_row, get_db, get_row, insert_row, update_row
from ..services import find_conflict
from ..utils import (
    blank_fields,
    error,
    get_json_object,
    is_int,
    is_number,
    missing_fields,
    parse_date,
)

bp = Blueprint("apartments", __name__, url_prefix="/apartments")

FIELDS = ("owner_id", "title", "address", "rooms", "capacity", "price_per_night", "status")
REQUIRED = ("owner_id", "title", "address", "rooms", "capacity", "price_per_night")
STATUSES = ("active", "maintenance")


def validate(data, partial):
    if not partial:
        missing = missing_fields(data, REQUIRED)
        if missing:
            return "missing required fields: " + ", ".join(missing)
    blank = blank_fields(data, ("title", "address"))
    if blank:
        return "fields must not be empty: " + ", ".join(blank)
    if "owner_id" in data:
        if not is_int(data["owner_id"]) or get_row("owners", data["owner_id"]) is None:
            return "owner not found"
    if "rooms" in data and not is_int(data["rooms"], 1):
        return "rooms must be an integer >= 1"
    if "capacity" in data and not is_int(data["capacity"], 1):
        return "capacity must be an integer >= 1"
    if "price_per_night" in data:
        price = data["price_per_night"]
        if not is_number(price) or price <= 0:
            return "price_per_night must be a number > 0"
    if "status" in data and data["status"] not in STATUSES:
        return "status must be one of: " + ", ".join(STATUSES)
    return None


@bp.post("")
def create_apartment():
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=False)
    if problem:
        return error(problem)
    values = {name: data[name] for name in FIELDS if name in data}
    apartment_id = insert_row("apartments", values)
    return jsonify(dict(get_row("apartments", apartment_id))), 201


@bp.get("")
def list_apartments():
    """Фильтры (необязательные): ?status=active&owner_id=1&min_capacity=3"""
    clauses, params = [], []
    if "status" in request.args:
        clauses.append("status = ?")
        params.append(request.args["status"])
    if "owner_id" in request.args:
        clauses.append("owner_id = ?")
        params.append(request.args["owner_id"])
    if "min_capacity" in request.args:
        clauses.append("capacity >= ?")
        params.append(request.args["min_capacity"])
    query = "SELECT * FROM apartments"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    rows = get_db().execute(query + " ORDER BY id", params).fetchall()
    return jsonify([dict(row) for row in rows])


@bp.get("/<int:apartment_id>")
def get_apartment(apartment_id):
    row = get_row("apartments", apartment_id)
    if row is None:
        return error("apartment not found", 404)
    return jsonify(dict(row))


@bp.put("/<int:apartment_id>")
def update_apartment(apartment_id):
    if get_row("apartments", apartment_id) is None:
        return error("apartment not found", 404)
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=True)
    if problem:
        return error(problem)
    values = {name: data[name] for name in FIELDS if name in data}
    update_row("apartments", apartment_id, values)
    return jsonify(dict(get_row("apartments", apartment_id)))


@bp.delete("/<int:apartment_id>")
def delete_apartment(apartment_id):
    if get_row("apartments", apartment_id) is None:
        return error("apartment not found", 404)
    try:
        delete_row("apartments", apartment_id)
    except sqlite3.IntegrityError:
        return error("apartment has bookings and cannot be deleted", 409)
    return "", 204


@bp.get("/<int:apartment_id>/availability")
def availability(apartment_id):
    """Свободна ли квартира: ?check_in=2026-10-01&check_out=2026-10-05"""
    apartment = get_row("apartments", apartment_id)
    if apartment is None:
        return error("apartment not found", 404)
    check_in = parse_date(request.args.get("check_in"))
    check_out = parse_date(request.args.get("check_out"))
    if check_in is None or check_out is None or check_out <= check_in:
        return error("check_in and check_out must be dates: YYYY-MM-DD, check_out > check_in")
    free = (
        apartment["status"] == "active"
        and find_conflict(apartment_id, check_in.isoformat(), check_out.isoformat()) is None
    )
    return jsonify(
        {
            "apartment_id": apartment_id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "available": free,
        }
    )
