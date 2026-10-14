from flask import Blueprint, request, jsonify
from app.db import get_connection, row_to_dict, rows_to_list
from app.utils import error, missing_fields

bp = Blueprint("clients", __name__, url_prefix="/clients")


@bp.get("")
def list_clients():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM clients ORDER BY id").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))


@bp.get("/<int:item_id>")
def get_client(item_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if row is None:
        return error("client not found", 404)
    return jsonify(row_to_dict(row))


@bp.post("")
def create_client():
    data = request.get_json(silent=True) or {}
    missing = missing_fields(data, ["full_name", "phone", "email"])
    if missing:
        return error(f"missing fields: {', '.join(missing)}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO clients (full_name, phone, email) VALUES (?, ?, ?)",
        (data["full_name"], data["phone"], data["email"]),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201


@bp.put("/<int:item_id>")
def update_client(item_id):
    data = request.get_json(silent=True) or {}
    conn = get_connection()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        conn.close()
        return error("client not found", 404)
    updated = dict(row)
    updated.update({k: v for k, v in data.items() if k in ["full_name", "phone", "email"]})
    conn.execute(
        "UPDATE clients SET full_name = ?, phone = ?, email = ? WHERE id = ?",
        (updated["full_name"], updated["phone"], updated["email"],  item_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row))


@bp.delete("/<int:item_id>")
def delete_client(item_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        conn.close()
        return error("client not found", 404)
    conn.execute("DELETE FROM clients WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return "", 204
