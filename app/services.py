"""Бизнес-логика, общая для нескольких модулей."""
from .db import get_db


def find_conflict(apartment_id, check_in, check_out, exclude_booking_id=None):
    """Ищет бронирование, пересекающееся с периодом [check_in, check_out).

    Отменённые бронирования не учитываются. Заезд в день выезда предыдущего
    гостя разрешён (check_out одной брони == check_in следующей).
    """
    query = (
        "SELECT id FROM bookings "
        "WHERE apartment_id = ? AND status != 'cancelled' "
        "AND check_in <= ? AND check_out >= ?"
    )
    params = [apartment_id, check_out, check_in]
    if exclude_booking_id is not None:
        query += " AND id != ?"
        params.append(exclude_booking_id)
    return get_db().execute(query, params).fetchone()
