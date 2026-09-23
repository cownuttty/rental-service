from tests.base import ApiTestCase


class ApartmentCrudTests(ApiTestCase):
    def test_create_apartment(self):
        owner = self.make_owner()
        response = self.client.post(
            "/apartments",
            json={
                "owner_id": owner["id"],
                "title": "Двушка на набережной",
                "address": "Сочи, Морская, 5",
                "rooms": 2,
                "capacity": 4,
                "price_per_night": 5500.5,
            },
        )
        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["status"], "active")
        self.assertEqual(body["price_per_night"], 5500.5)

    def test_create_apartment_unknown_owner(self):
        response = self.client.post(
            "/apartments",
            json={
                "owner_id": 999,
                "title": "X",
                "address": "Y",
                "rooms": 1,
                "capacity": 1,
                "price_per_night": 100,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("owner", response.get_json()["error"])

    def test_create_apartment_invalid_values(self):
        owner = self.make_owner()
        base = {
            "owner_id": owner["id"],
            "title": "X",
            "address": "Y",
            "rooms": 1,
            "capacity": 1,
            "price_per_night": 100,
        }
        for field, value in (("price_per_night", 0), ("rooms", 0), ("capacity", -3),
                             ("status", "broken")):
            with self.subTest(field=field):
                response = self.client.post("/apartments", json={**base, field: value})
                self.assertEqual(response.status_code, 400)

    def test_list_and_filter_apartments(self):
        owner = self.make_owner()
        self.make_apartment(owner_id=owner["id"], capacity=2)
        self.make_apartment(owner_id=owner["id"], capacity=5)
        self.assertEqual(len(self.client.get("/apartments").get_json()), 2)
        big = self.client.get("/apartments?min_capacity=4").get_json()
        self.assertEqual(len(big), 1)
        self.assertEqual(big[0]["capacity"], 5)

    def test_filter_by_status(self):
        owner = self.make_owner()
        self.make_apartment(owner_id=owner["id"])
        self.make_apartment(owner_id=owner["id"], status="maintenance")
        result = self.client.get("/apartments?status=maintenance").get_json()
        self.assertEqual(len(result), 1)

    def test_get_apartment(self):
        apartment = self.make_apartment()
        response = self.client.get(f"/apartments/{apartment['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["title"], "Студия у метро")

    def test_get_apartment_not_found(self):
        self.assertEqual(self.client.get("/apartments/999").status_code, 404)

    def test_update_apartment(self):
        apartment = self.make_apartment()
        response = self.client.put(
            f"/apartments/{apartment['id']}",
            json={"price_per_night": 3500, "status": "maintenance"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["price_per_night"], 3500)
        self.assertEqual(body["status"], "maintenance")

    def test_delete_apartment(self):
        apartment = self.make_apartment()
        self.assertEqual(self.client.delete(f"/apartments/{apartment['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/apartments/{apartment['id']}").status_code, 404)

    def test_delete_apartment_with_bookings_is_forbidden(self):
        apartment = self.make_apartment()
        guest = self.make_client()
        self.make_booking(apartment["id"], guest["id"])
        response = self.client.delete(f"/apartments/{apartment['id']}")
        self.assertEqual(response.status_code, 409)


class AvailabilityTests(ApiTestCase):
    def test_free_apartment_is_available(self):
        apartment = self.make_apartment()
        response = self.client.get(
            f"/apartments/{apartment['id']}/availability?check_in=2026-10-01&check_out=2026-10-05"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["available"])

    def test_booked_apartment_is_not_available(self):
        apartment = self.make_apartment()
        guest = self.make_client()
        self.make_booking(apartment["id"], guest["id"])
        response = self.client.get(
            f"/apartments/{apartment['id']}/availability?check_in=2026-10-03&check_out=2026-10-06"
        )
        self.assertFalse(response.get_json()["available"])

    def test_availability_requires_valid_dates(self):
        apartment = self.make_apartment()
        response = self.client.get(f"/apartments/{apartment['id']}/availability?check_in=abc")
        self.assertEqual(response.status_code, 400)
