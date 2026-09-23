"""Клиенты (арендаторы): CRUD."""
import sqlite3

from flask import Blueprint, jsonify

from ..db import delete_row, get_db, get_row, insert_row, update_row
from ..utils import blank_fields, error, get_json_object, missing_fields

bp = Blueprint("clients", __name__, url_prefix="/clients")

FIELDS = ("full_name", "phone", "email")


def validate(data, partial):
    if not partial:
        missing = missing_fields(data, FIELDS)
        if missing:
            return "missing required fields: " + ", ".join(missing)
    blank = blank_fields(data, FIELDS)
    if blank:
        return "fields must not be empty: " + ", ".join(blank)
    if "email" in data and "@" not in str(data["email"]):
        return "email is invalid"
    return None


@bp.post("")
def create_client():
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=False)
    if problem:
        return error(problem)
    values = {name: data[name] for name in FIELDS}
    try:
        client_id = insert_row("clients", values)
    except sqlite3.IntegrityError:
        return error("client with this email already exists", 409)
    return jsonify(dict(get_row("clients", client_id))), 201


@bp.get("")
def list_clients():
    rows = get_db().execute("SELECT * FROM clients ORDER BY id").fetchall()
    return jsonify([dict(row) for row in rows])


@bp.get("/<int:client_id>")
def get_client(client_id):
    row = get_row("clients", client_id)
    if row is None:
        return error("client not found", 404)
    return jsonify(dict(row))


@bp.put("/<int:client_id>")
def update_client(client_id):
    if get_row("clients", client_id) is None:
        return error("client not found", 404)
    data = get_json_object()
    if data is None:
        return error("request body must be a JSON object")
    problem = validate(data, partial=True)
    if problem:
        return error(problem)
    values = {name: data[name] for name in FIELDS if name in data}
    try:
        update_row("clients", client_id, values)
    except sqlite3.IntegrityError:
        return error("client with this email already exists", 409)
    return jsonify(dict(get_row("clients", client_id)))


@bp.delete("/<int:client_id>")
def delete_client(client_id):
    if get_row("clients", client_id) is None:
        return error("client not found", 404)
    try:
        delete_row("clients", client_id)
    except sqlite3.IntegrityError:
        return error("client has bookings and cannot be deleted", 409)
    return "", 204
