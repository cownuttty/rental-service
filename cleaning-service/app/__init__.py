from flask import Flask, jsonify
from app.db import init_db


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False

    from app.routes import cleaners, cleaning_tasks
    app.register_blueprint(cleaners.bp)
    app.register_blueprint(cleaning_tasks.bp)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="cleaning-service")

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify(error="not found"), 404

    @app.errorhandler(405)
    def not_allowed(_e):
        return jsonify(error="method not allowed"), 405

    init_db()
    return app
