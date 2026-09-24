"""Сервис управляющей компании по аренде посуточных квартир (REST API на Flask)."""
import os

from flask import Flask, jsonify

from .db import close_db, init_db


def create_app(config=None):
    """Фабрика приложения. Тесты передают свой config (например, путь к временной БД)."""
    app = Flask(__name__)
    app.json.ensure_ascii = False  # русский текст в JSON читается как есть
    app.config["DATABASE"] = os.environ.get(
        "DATABASE_PATH", os.path.join(app.instance_path, "rental.db")
    )
    if config:
        app.config.update(config)

    os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)

    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()

    from .routes import apartments, bookings, cleaners, cleaning_tasks, clients, owners

    for module in (owners, apartments, clients, cleaners, bookings, cleaning_tasks):
        app.register_blueprint(module.bp)

    @app.get("/health")
    def health():
        """Проверка работоспособности (используется при деплое)."""
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "method not allowed"}), 405

    return app
