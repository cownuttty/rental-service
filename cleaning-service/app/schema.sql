CREATE TABLE IF NOT EXISTS cleaners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL
);

-- apartment_id, booking_id указывают на сущности сервиса rental-api.
-- Это обычная практика в микросервисах: вместо FOREIGN KEY (которого
-- физически не может быть - это другая база данных, в другом контейнере)
-- здесь просто хранится "чужой" числовой идентификатор.
CREATE TABLE IF NOT EXISTS cleaning_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    apartment_id INTEGER NOT NULL,
    booking_id INTEGER,
    cleaner_id INTEGER REFERENCES cleaners(id) ON DELETE SET NULL,
    scheduled_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned'
);
