from flask import Flask, jsonify
from app.db import init_db


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False

    from app.routes import owners, apartments, clients, bookings
    app.register_blueprint(owners.bp)
    app.register_blueprint(apartments.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(bookings.bp)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="rental-api")

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify(error="not found"), 404

    @app.errorhandler(405)
    def not_allowed(_e):
        return jsonify(error="method not allowed"), 405

    init_db()
    return app
