-- Схема базы данных сервиса посуточной аренды квартир (SQLite).
-- Скрипт выполняется при каждом старте приложения; IF NOT EXISTS делает его безопасным.

-- Собственники квартир
CREATE TABLE IF NOT EXISTS owners (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name          TEXT NOT NULL,
    phone              TEXT NOT NULL,
    email              TEXT NOT NULL UNIQUE,
    -- процент, который удерживает управляющая компания
    commission_percent REAL NOT NULL DEFAULT 20
        CHECK (commission_percent BETWEEN 0 AND 100)
);

-- Квартиры (принадлежат собственнику, сдаются через управляющую компанию)
CREATE TABLE IF NOT EXISTS apartments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id        INTEGER NOT NULL REFERENCES owners (id) ON DELETE RESTRICT,
    title           TEXT NOT NULL,
    address         TEXT NOT NULL,
    rooms           INTEGER NOT NULL CHECK (rooms >= 1),
    capacity        INTEGER NOT NULL CHECK (capacity >= 1),
    price_per_night REAL NOT NULL CHECK (price_per_night > 0),
    status          TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'maintenance'))
);

-- Клиенты (арендаторы)
CREATE TABLE IF NOT EXISTS clients (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone     TEXT NOT NULL,
    email     TEXT NOT NULL UNIQUE
);

-- Горничные
CREATE TABLE IF NOT EXISTS cleaners (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone     TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- Бронирования
CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    apartment_id INTEGER NOT NULL REFERENCES apartments (id) ON DELETE RESTRICT,
    client_id    INTEGER NOT NULL REFERENCES clients (id) ON DELETE RESTRICT,
    check_in     TEXT NOT NULL,           -- дата заезда, YYYY-MM-DD
    check_out    TEXT NOT NULL,           -- дата выезда, YYYY-MM-DD
    guests       INTEGER NOT NULL CHECK (guests >= 1),
    total_price  REAL NOT NULL,
    status       TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'confirmed', 'cancelled', 'completed')),
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (check_out > check_in)
);

-- Задачи на уборку (горничные убирают квартиры после выезда гостей)
CREATE TABLE IF NOT EXISTS cleaning_tasks (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    apartment_id   INTEGER NOT NULL REFERENCES apartments (id) ON DELETE CASCADE,
    booking_id     INTEGER REFERENCES bookings (id) ON DELETE SET NULL,
    cleaner_id     INTEGER REFERENCES cleaners (id) ON DELETE SET NULL,
    scheduled_date TEXT NOT NULL,          -- дата уборки, YYYY-MM-DD
    status         TEXT NOT NULL DEFAULT 'planned'
        CHECK (status IN ('planned', 'in_progress', 'done')),
    cost           REAL NOT NULL DEFAULT 0 CHECK (cost >= 0)
);
