"""Задачи на уборку: CRUD + автоматическое создание после завершения бронирования."""
from flask import Blueprint, jsonify, request

from ..db import delete_row, get_db, get_row, insert_row, update_row
from ..utils import error, get_json_object, is_int, is_number, missing_fields, parse_date

bp = Blueprint("cleaning_tasks", __name__, url_prefix="/cleaning-tasks")

FIELDS = ("apartment_id", "booking_id", "cleaner_id", "scheduled_date", "status", "cost")
REQUIRED = ("apartment_id", "scheduled_date")
STATUSES = ("planned", "in_progress", "done")


def validate(data, partial):
    if not partial:
        missing = missing_fields(data, REQUIRED)
        if missing:
            return "missing required fields: " + ", ".join(missing)
    if "apartment_id" in data:
        if not is_int(data["apartment_id"]) or get_row("apartments", data["apartment_id"]) is None:
            return "apartment not found"
    if data.get("booking_id") is not None:
        if not is_int(data["booking_id"]) or get_row("bookings", data["booking_id"]) is None:
            return "booking not found"
    if data.get("cleaner_id") is not None:
        cleaner = get_row("cleaners", data["cleaner_id"]) if is_int(data["cleaner_id"]) else None
        if cleaner is None or not cleaner["is_active"]:
            return "cleaner not found or inactive"
    if "scheduled_date" in data and parse_date(data["scheduled_date"]) is None:
        return "scheduled_date must be a date in YYYY-MM-DD format"
    if "status" in data and data["status"] not in STATUSES:
        return "status must be one of: " + ", ".join(STATUSES)
    if "cost" in data and not is_number(data["cost"], 0):
        return "cost must be a number >= 0"
    return None


def create_task_for_booking(booking_id):
    """Создаёт задачу на уборку в день выезда гостя (если её ещё нет)."""
    booking = get_row("bookings", booking_id)
    exists = get_db().execute(
        "SELECT id FROM cleaning_tasks WHERE booking_id = ?", (booking_id,)
    ).fetchone()
    if booking is None or exists:
        return None
    return insert_row(
        "cleaning_tasks",
        {
            "apartment_id": booking["apartment_id"],
            "booking_id": booking_id,
            "scheduled_date": booking["check_out"],
        },
    )


@bp.post("")
def create_task():
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=False)
    if problem:
        return error(problem)
    values = {name: data[name] for name in FIELDS if name in data}
    task_id = insert_row("cleaning_tasks", values)
    return jsonify(dict(get_row("cleaning_tasks", task_id))), 201


@bp.get("")
def list_tasks():
    """Фильтры (необязательные): ?cleaner_id=1&apartment_id=2&status=planned&date=2026-10-05"""
    clauses, params = [], []
    for name in ("cleaner_id", "apartment_id", "status"):
        if name in request.args:
            clauses.append(f"{name} = ?")
            params.append(request.args[name])
    if "date" in request.args:
        clauses.append("scheduled_date = ?")
        params.append(request.args["date"])
    query = "SELECT * FROM cleaning_tasks"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    rows = get_db().execute(query + " ORDER BY scheduled_date, id", params).fetchall()
    return jsonify([dict(row) for row in rows])


@bp.get("/<int:task_id>")
def get_task(task_id):
    row = get_row("cleaning_tasks", task_id)
    if row is None:
        return error("cleaning task not found", 404)
    return jsonify(dict(row))


@bp.put("/<int:task_id>")
def update_task(task_id):
    if get_row("cleaning_tasks", task_id) is None:
        return error("cleaning task not found", 404)
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=True)
    if problem:
        return error(problem)
    values = {name: data[name] for name in FIELDS if name in data}
    update_row("cleaning_tasks", task_id, values)
    return jsonify(dict(get_row("cleaning_tasks", task_id)))


@bp.delete("/<int:task_id>")
def delete_task(task_id):
    if get_row("cleaning_tasks", task_id) is None:
        return error("cleaning task not found", 404)
    delete_row("cleaning_tasks", task_id)
    return "", 204
