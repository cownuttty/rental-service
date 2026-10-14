import os
import tempfile
import unittest


class RentalApiSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["DB_PATH"] = os.path.join(self.tmpdir.name, "test.db")
        from app import create_app
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["service"], "rental-api")

    def test_owner_crud(self):
        resp = self.client.post("/owners", json={
            "full_name": "Иванов Иван", "phone": "+79990000000", "email": "ivanov@example.com"
        })
        self.assertEqual(resp.status_code, 201)
        owner_id = resp.get_json()["id"]

        resp = self.client.get(f"/owners/{owner_id}")
        self.assertEqual(resp.status_code, 200)

        resp = self.client.put(f"/owners/{owner_id}", json={"phone": "+79991111111"})
        self.assertEqual(resp.get_json()["phone"], "+79991111111")

        resp = self.client.delete(f"/owners/{owner_id}")
        self.assertEqual(resp.status_code, 204)

    def test_booking_conflict(self):
        owner = self.client.post("/owners", json={
            "full_name": "A", "phone": "1", "email": "a@a.com"
        }).get_json()
        apt = self.client.post("/apartments", json={
            "owner_id": owner["id"], "address": "ул. Ленина, 1", "rooms": 2, "price_per_night": 2000
        }).get_json()
        client_ = self.client.post("/clients", json={
            "full_name": "B", "phone": "2", "email": "b@b.com"
        }).get_json()

        resp = self.client.post("/bookings", json={
            "apartment_id": apt["id"], "client_id": client_["id"],
            "check_in": "2026-10-20", "check_out": "2026-10-25"
        })
        self.assertEqual(resp.status_code, 201)

        conflict = self.client.post("/bookings", json={
            "apartment_id": apt["id"], "client_id": client_["id"],
            "check_in": "2026-10-22", "check_out": "2026-10-26"
        })
        self.assertEqual(conflict.status_code, 409)


if __name__ == "__main__":
    unittest.main()
