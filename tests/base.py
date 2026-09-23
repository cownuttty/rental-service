"""Общий базовый класс для тестов: чистая временная БД на каждый тест + помощники."""
import os
import tempfile
import unittest

from app import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        # Для каждого теста — новая пустая база в отдельной временной папке
        self._tmp = tempfile.TemporaryDirectory()
        self.app = create_app(
            {"TESTING": True, "DATABASE": os.path.join(self._tmp.name, "test.db")}
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self._tmp.cleanup()

    # ---- помощники: создают записи и возвращают их JSON ----

    def _create(self, url, payload):
        response = self.client.post(url, json=payload)
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def make_owner(self, **overrides):
        payload = {
            "full_name": "Иван Петров",
            "phone": "+7 900 111-22-33",
            "email": "ivan@example.com",
            "commission_percent": 20,
        }
        payload.update(overrides)
        return self._create("/owners", payload)

    def make_apartment(self, owner_id=None, **overrides):
        if owner_id is None:
            owner_id = self.make_owner()["id"]
        payload = {
            "owner_id": owner_id,
            "title": "Студия у метро",
            "address": "Москва, ул. Ленина, 1",
            "rooms": 1,
            "capacity": 2,
            "price_per_night": 3000,
        }
        payload.update(overrides)
        return self._create("/apartments", payload)

    def make_client(self, **overrides):
        payload = {
            "full_name": "Анна Смирнова",
            "phone": "+7 900 555-66-77",
            "email": "anna@example.com",
        }
        payload.update(overrides)
        return self._create("/clients", payload)

    def make_cleaner(self, **overrides):
        payload = {"full_name": "Мария Иванова", "phone": "+7 900 000-11-22"}
        payload.update(overrides)
        return self._create("/cleaners", payload)

    def make_booking(self, apartment_id, client_id, **overrides):
        payload = {
            "apartment_id": apartment_id,
            "client_id": client_id,
            "check_in": "2026-10-01",
            "check_out": "2026-10-05",
            "guests": 2,
        }
        payload.update(overrides)
        return self._create("/bookings", payload)
