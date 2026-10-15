from flask import Blueprint, request, jsonify
from app.db import get_connection, row_to_dict, rows_to_list
from app.utils import error, missing_fields

bp = Blueprint("cleaning_tasks", __name__, url_prefix="/cleaning-tasks")


@bp.get("")
def list_tasks():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cleaning_tasks ORDER BY scheduled_date, id").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))
    #return jsonify([{**row, "note": "для демонстрации"} for row in rows_to_list(rows)])


@bp.get("/<int:task_id>")
def get_task(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM cleaning_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        return error("task not found", 404)
    return jsonify(row_to_dict(row))


@bp.post("")
def create_task():
    """Эту ручку вызывает либо сам пользователь, либо сервис rental-api
    (см. app/routes/bookings.py -> notify_cleaning_service) при переводе
    бронирования в статус completed."""
    data = request.get_json(silent=True) or {}
    missing = missing_fields(data, ["apartment_id", "scheduled_date"])
    if missing:
        return error(f"missing fields: {', '.join(missing)}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO cleaning_tasks (apartment_id, booking_id, cleaner_id, scheduled_date, status) "
        "VALUES (?, ?, ?, ?, 'planned')",
        (data["apartment_id"], data.get("booking_id"), data.get("cleaner_id"), data["scheduled_date"]),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM cleaning_tasks WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201


@bp.put("/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    conn = get_connection()
    row = conn.execute("SELECT * FROM cleaning_tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        return error("task not found", 404)
    updated = dict(row)
    updated.update({k: v for k, v in data.items() if k in ("cleaner_id", "scheduled_date", "status")})
    conn.execute(
        "UPDATE cleaning_tasks SET cleaner_id = ?, scheduled_date = ?, status = ? WHERE id = ?",
        (updated["cleaner_id"], updated["scheduled_date"], updated["status"], task_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM cleaning_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row))


@bp.delete("/<int:task_id>")
def delete_task(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM cleaning_tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        return error("task not found", 404)
    conn.execute("DELETE FROM cleaning_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return "", 204
