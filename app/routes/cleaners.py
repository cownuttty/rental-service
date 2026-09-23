"""Горничные: CRUD."""
from flask import Blueprint, jsonify

from ..db import delete_row, get_db, get_row, insert_row, update_row
from ..utils import blank_fields, error, get_json_object, missing_fields

bp = Blueprint("cleaners", __name__, url_prefix="/cleaners")

FIELDS = ("full_name", "phone", "is_active")
REQUIRED = ("full_name", "phone")


def to_json(row):
    """В БД is_active хранится как 0/1, наружу отдаём true/false."""
    item = dict(row)
    item["is_active"] = bool(item["is_active"])
    return item


def validate(data, partial):
    if not partial:
        missing = missing_fields(data, REQUIRED)
        if missing:
            return "missing required fields: " + ", ".join(missing)
    blank = blank_fields(data, REQUIRED)
    if blank:
        return "fields must not be empty: " + ", ".join(blank)
    if "is_active" in data and not isinstance(data["is_active"], bool):
        return "is_active must be true or false"
    return None


def collect_values(data):
    values = {name: data[name] for name in FIELDS if name in data}
    if "is_active" in values:
        values["is_active"] = int(values["is_active"])
    return values


@bp.post("")
def create_cleaner():
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=False)
    if problem:
        return error(problem)
    cleaner_id = insert_row("cleaners", collect_values(data))
    return jsonify(to_json(get_row("cleaners", cleaner_id))), 201


@bp.get("")
def list_cleaners():
    rows = get_db().execute("SELECT * FROM cleaners ORDER BY id").fetchall()
    return jsonify([to_json(row) for row in rows])


@bp.get("/<int:cleaner_id>")
def get_cleaner(cleaner_id):
    row = get_row("cleaners", cleaner_id)
    if row is None:
        return error("cleaner not found", 404)
    return jsonify(to_json(row))


@bp.put("/<int:cleaner_id>")
def update_cleaner(cleaner_id):
    if get_row("cleaners", cleaner_id) is None:
        return error("cleaner not found", 404)
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=True)
    if problem:
        return error(problem)
    update_row("cleaners", cleaner_id, collect_values(data))
    return jsonify(to_json(get_row("cleaners", cleaner_id)))


@bp.delete("/<int:cleaner_id>")
def delete_cleaner(cleaner_id):
    if get_row("cleaners", cleaner_id) is None:
        return error("cleaner not found", 404)
    delete_row("cleaners", cleaner_id)
    return "", 204
