import os
import requests
from flask import Blueprint, request, jsonify
from app.db import get_connection, row_to_dict, rows_to_list
from app.utils import error, missing_fields

bp = Blueprint("bookings", __name__, url_prefix="/bookings")

# Адрес сервиса горничных/уборок. В docker-compose это имя сервиса
# "cleaning-service" (Docker Compose сам настраивает DNS внутри сети).
CLEANING_SERVICE_URL = os.environ.get("CLEANING_SERVICE_URL", "http://cleaning-service:5001")


def has_conflict(conn, apartment_id, check_in, check_out, exclude_id=None):
    query = (
        "SELECT COUNT(*) AS cnt FROM bookings "
        "WHERE apartment_id = ? AND status != 'cancelled' "
        "AND check_in < ? AND check_out > ?"
    )
    params = [apartment_id, check_out, check_in]
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
    row = conn.execute(query, params).fetchone()
    return row["cnt"] > 0


def notify_cleaning_service(booking):
    """Сообщает микросервису уборок, что квартиру нужно убрать после выезда.

    Это и есть пример межсервисного взаимодействия в микросервисной
    архитектуре: rental-api не трогает таблицы cleaning-service напрямую
    (у него вообще нет к ним доступа - это ДРУГАЯ база данных в ДРУГОМ
    контейнере), а посылает ему HTTP-запрос.
    """
    try:
        requests.post(
            f"{CLEANING_SERVICE_URL}/cleaning-tasks",
            json={
                "apartment_id": booking["apartment_id"],
                "booking_id": booking["id"],
                "scheduled_date": booking["check_out"],
            },
            timeout=5,
        )
    except requests.RequestException as exc:
        # В учебном проекте не валим основной запрос, если сервис уборок
        # временно недоступен - просто логируем. В реальной системе здесь
        # обычно используется очередь сообщений (RabbitMQ/Kafka) вместо
        # прямого HTTP-вызова, чтобы не терять события.
        print(f"[rental-api] cleaning-service unavailable: {exc}")


@bp.get("")
def list_bookings():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM bookings ORDER BY id").fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))


@bp.get("/<int:booking_id>")
def get_booking(booking_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    conn.close()
    if row is None:
        return error("booking not found", 404)
    return jsonify(row_to_dict(row))


@bp.post("")
def create_booking():
    data = request.get_json(silent=True) or {}
    missing = missing_fields(data, ["apartment_id", "client_id", "check_in", "check_out"])
    if missing:
        return error(f"missing fields: {', '.join(missing)}")
    conn = get_connection()
    if has_conflict(conn, data["apartment_id"], data["check_in"], data["check_out"]):
        conn.close()
        return error("apartment already booked for these dates", 409)
    cur = conn.execute(
        "INSERT INTO bookings (apartment_id, client_id, check_in, check_out, status) "
        "VALUES (?, ?, ?, ?, 'booked')",
        (data["apartment_id"], data["client_id"], data["check_in"], data["check_out"]),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM bookings WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201


@bp.put("/<int:booking_id>")
def update_booking(booking_id):
    data = request.get_json(silent=True) or {}
    conn = get_connection()
    row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if row is None:
        conn.close()
        return error("booking not found", 404)
    previous_status = row["status"]
    updated = dict(row)
    updated.update({k: v for k, v in data.items() if k in ("check_in", "check_out", "status")})
    conn.execute(
        "UPDATE bookings SET check_in = ?, check_out = ?, status = ? WHERE id = ?",
        (updated["check_in"], updated["check_out"], updated["status"], booking_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    conn.close()
    if previous_status != "completed" and row["status"] == "completed":
        notify_cleaning_service(row)
    return jsonify(row_to_dict(row))


@bp.delete("/<int:booking_id>")
def delete_booking(booking_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if row is None:
        conn.close()
        return error("booking not found", 404)
    conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return "", 204
