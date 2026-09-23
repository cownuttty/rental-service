"""Точка входа: запуск сервиса аренды посуточных квартир."""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))

    if os.environ.get("APP_ENV") == "production":
        # Боевой режим (так приложение запускает Jenkins при деплое)
        from waitress import serve

        serve(app, host=host, port=port)
    else:
        # Режим разработки: автоперезагрузка и подробные ошибки
        app.run(host=host, port=port, debug=True)
