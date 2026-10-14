from flask import Blueprint, request, jsonify
from app.db import get_connection, row_to_dict, rows_to_list
from app.utils import error, missing_fields

bp = Blueprint("cleaners", __name__, url_prefix="/cleaners")


#@bp.get("")
#def list_cleaners():
#    conn = get_connection()
#    rows = conn.execute("SELECT * FROM cleaners ORDER BY id").fetchall()
#    conn.close()
#    return jsonify(rows_to_list(rows))

@bp.get("")
def list_cleaners():
    conn = get_connection()
    rows = conn.execute(
        "SELECT c.id, c.full_name, c.phone, "
        "       COUNT(t.id) AS tasks_count "
        "FROM cleaners c "
        "LEFT JOIN cleaning_tasks t ON t.cleaner_id = c.id "
        "GROUP BY c.id "
        "ORDER BY c.id"
    ).fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))


@bp.get("/<int:cleaner_id>")
def get_cleaner(cleaner_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM cleaners WHERE id = ?", (cleaner_id,)).fetchone()
    conn.close()
    if row is None:
        return error("cleaner not found", 404)
    return jsonify(row_to_dict(row))


@bp.post("")
def create_cleaner():
    data = request.get_json(silent=True) or {}
    missing = missing_fields(data, ["full_name", "phone"])
    if missing:
        return error(f"missing fields: {', '.join(missing)}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO cleaners (full_name, phone) VALUES (?, ?)",
        (data["full_name"], data["phone"]),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM cleaners WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201


@bp.put("/<int:cleaner_id>")
def update_cleaner(cleaner_id):
    data = request.get_json(silent=True) or {}
    conn = get_connection()
    row = conn.execute("SELECT * FROM cleaners WHERE id = ?", (cleaner_id,)).fetchone()
    if row is None:
        conn.close()
        return error("cleaner not found", 404)
    updated = dict(row)
    updated.update({k: v for k, v in data.items() if k in ("full_name", "phone")})
    conn.execute(
        "UPDATE cleaners SET full_name = ?, phone = ? WHERE id = ?",
        (updated["full_name"], updated["phone"], cleaner_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM cleaners WHERE id = ?", (cleaner_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row))


@bp.delete("/<int:cleaner_id>")
def delete_cleaner(cleaner_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM cleaners WHERE id = ?", (cleaner_id,)).fetchone()
    if row is None:
        conn.close()
        return error("cleaner not found", 404)
    conn.execute("DELETE FROM cleaners WHERE id = ?", (cleaner_id,))
    conn.commit()
    conn.close()
    return "", 204
