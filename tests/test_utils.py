"""Модульные тесты вспомогательных функций (без HTTP и без БД)."""
import unittest
from datetime import date

from app.utils import is_int, is_number, missing_fields, parse_date


class UtilsTests(unittest.TestCase):
    def test_parse_date_valid(self):
        self.assertEqual(parse_date("2026-10-01"), date(2026, 10, 1))

    def test_parse_date_invalid(self):
        for value in ("2026-13-01", "01.10.2026", "20261001", None, 20261001):
            with self.subTest(value=value):
                self.assertIsNone(parse_date(value))

    def test_is_number_bounds(self):
        self.assertTrue(is_number(20, 0, 100))
        self.assertFalse(is_number(101, 0, 100))
        self.assertFalse(is_number("20"))
        self.assertFalse(is_number(True))

    def test_is_int(self):
        self.assertTrue(is_int(3, 1))
        self.assertFalse(is_int(0, 1))
        self.assertFalse(is_int(2.5))

    def test_missing_fields(self):
        data = {"a": "x", "b": "  ", "c": None}
        self.assertEqual(missing_fields(data, ("a", "b", "c", "d")), ["b", "c", "d"])
