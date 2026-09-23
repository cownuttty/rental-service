"""Работа с базой данных SQLite: подключение и небольшие помощники для SQL-запросов."""
import sqlite3

from flask import current_app, g


def get_db():
    """Возвращает подключение к БД, одно на каждый HTTP-запрос."""
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row  # строки можно превращать в dict
        connection.execute("PRAGMA foreign_keys = ON")  # SQLite по умолчанию не проверяет FK
        g.db = connection
    return g.db


def close_db(_error=None):
    """Закрывает подключение в конце запроса."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    """Создаёт таблицы из schema.sql (если их ещё нет)."""
    with current_app.open_resource("schema.sql") as schema:
        get_db().executescript(schema.read().decode("utf-8"))


# Имена таблиц и колонок ниже всегда приходят из нашего кода (белые списки в routes),
# а значения передаются через "?" — поэтому SQL-инъекция невозможна.

def get_row(table, row_id):
    return get_db().execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()


def insert_row(table, values):
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    db = get_db()
    cursor = db.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(values.values())
    )
    db.commit()
    return cursor.lastrowid


def update_row(table, row_id, values):
    if not values:
        return
    assignments = ", ".join(f"{column} = ?" for column in values)
    db = get_db()
    db.execute(
        f"UPDATE {table} SET {assignments} WHERE id = ?", (*values.values(), row_id)
    )
    db.commit()


def delete_row(table, row_id):
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    db.commit()
