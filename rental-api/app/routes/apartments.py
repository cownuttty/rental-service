from flask import Blueprint, request, jsonify
from app.db import get_connection, row_to_dict, rows_to_list
from app.utils import error, missing_fields

bp = Blueprint("apartments", __name__, url_prefix="/apartments")


@bp.get("")
def list_apartments():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM apartments ORDER BY id").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))


@bp.get("/<int:item_id>")
def get_apartment(item_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM apartments WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if row is None:
        return error("apartment not found", 404)
    return jsonify(row_to_dict(row))


@bp.post("")
def create_apartment():
    data = request.get_json(silent=True) or {}
    missing = missing_fields(data, ["owner_id", "address", "rooms", "price_per_night"])
    if missing:
        return error(f"missing fields: {', '.join(missing)}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO apartments (owner_id, address, rooms, price_per_night) VALUES (?, ?, ?, ?)",
        (data["owner_id"], data["address"], data["rooms"], data["price_per_night"]),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM apartments WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201


@bp.put("/<int:item_id>")
def update_apartment(item_id):
    data = request.get_json(silent=True) or {}
    conn = get_connection()
    row = conn.execute("SELECT * FROM apartments WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        conn.close()
        return error("apartment not found", 404)
    updated = dict(row)
    updated.update({k: v for k, v in data.items() if k in ["owner_id", "address", "rooms", "price_per_night"]})
    conn.execute(
        "UPDATE apartments SET owner_id = ?, address = ?, rooms = ?, price_per_night = ? WHERE id = ?",
        (updated["owner_id"], updated["address"], updated["rooms"], updated["price_per_night"],  item_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM apartments WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row))


@bp.delete("/<int:item_id>")
def delete_apartment(item_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM apartments WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        conn.close()
        return error("apartment not found", 404)
    conn.execute("DELETE FROM apartments WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return "", 204
