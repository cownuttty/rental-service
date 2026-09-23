from tests.base import ApiTestCase


class BookingCrudTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.apartment = self.make_apartment(capacity=3, price_per_night=2000)
        self.guest = self.make_client()

    def test_create_booking_calculates_total_price(self):
        booking = self.make_booking(self.apartment["id"], self.guest["id"])  # 4 ночи
        self.assertEqual(booking["total_price"], 8000)
        self.assertEqual(booking["status"], "new")

    def test_create_booking_missing_fields(self):
        response = self.client.post("/bookings", json={"apartment_id": self.apartment["id"]})
        self.assertEqual(response.status_code, 400)

    def test_create_booking_unknown_apartment_or_client(self):
        payload = {"apartment_id": 999, "client_id": self.guest["id"],
                   "check_in": "2026-10-01", "check_out": "2026-10-02"}
        self.assertEqual(self.client.post("/bookings", json=payload).status_code, 400)
        payload.update(apartment_id=self.apartment["id"], client_id=999)
        self.assertEqual(self.client.post("/bookings", json=payload).status_code, 400)

    def test_check_out_must_be_after_check_in(self):
        for check_in, check_out in (("2026-10-05", "2026-10-05"), ("2026-10-05", "2026-10-01")):
            with self.subTest(check_in=check_in, check_out=check_out):
                response = self.client.post(
                    "/bookings",
                    json={"apartment_id": self.apartment["id"], "client_id": self.guest["id"],
                          "check_in": check_in, "check_out": check_out},
                )
                self.assertEqual(response.status_code, 400)

    def test_invalid_date_format(self):
        response = self.client.post(
            "/bookings",
            json={"apartment_id": self.apartment["id"], "client_id": self.guest["id"],
                  "check_in": "01.10.2026", "check_out": "05.10.2026"},
        )
        self.assertEqual(response.status_code, 400)

    def test_too_many_guests(self):
        response = self.client.post(
            "/bookings",
            json={"apartment_id": self.apartment["id"], "client_id": self.guest["id"],
                  "check_in": "2026-10-01", "check_out": "2026-10-05", "guests": 10},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("capacity", response.get_json()["error"])

    def test_apartment_under_maintenance_cannot_be_booked(self):
        self.client.put(f"/apartments/{self.apartment['id']}", json={"status": "maintenance"})
        response = self.client.post(
            "/bookings",
            json={"apartment_id": self.apartment["id"], "client_id": self.guest["id"],
                  "check_in": "2026-10-01", "check_out": "2026-10-05"},
        )
        self.assertEqual(response.status_code, 409)

    def test_overlapping_booking_is_rejected(self):
        self.make_booking(self.apartment["id"], self.guest["id"])  # 01.10 - 05.10
        response = self.client.post(
            "/bookings",
            json={"apartment_id": self.apartment["id"], "client_id": self.guest["id"],
                  "check_in": "2026-10-03", "check_out": "2026-10-07"},
        )
        self.assertEqual(response.status_code, 409)

    def test_back_to_back_bookings_are_allowed(self):
        """Заезд в день выезда предыдущего гостя — это не пересечение."""
        self.make_booking(self.apartment["id"], self.guest["id"])  # 01.10 - 05.10
        second = self.make_booking(
            self.apartment["id"], self.guest["id"], check_in="2026-10-05", check_out="2026-10-08"
        )
        self.assertEqual(second["total_price"], 6000)

    def test_cancelled_booking_does_not_block_dates(self):
        first = self.make_booking(self.apartment["id"], self.guest["id"])
        self.client.put(f"/bookings/{first['id']}", json={"status": "cancelled"})
        again = self.make_booking(self.apartment["id"], self.guest["id"])
        self.assertEqual(again["status"], "new")

    def test_list_and_filter_bookings(self):
        other = self.make_apartment(owner_id=self.apartment["owner_id"], title="Другая")
        self.make_booking(self.apartment["id"], self.guest["id"])
        self.make_booking(other["id"], self.guest["id"])
        self.assertEqual(len(self.client.get("/bookings").get_json()), 2)
        filtered = self.client.get(f"/bookings?apartment_id={other['id']}").get_json()
        self.assertEqual(len(filtered), 1)

    def test_get_booking(self):
        booking = self.make_booking(self.apartment["id"], self.guest["id"])
        response = self.client.get(f"/bookings/{booking['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["guests"], 2)

    def test_get_booking_not_found(self):
        self.assertEqual(self.client.get("/bookings/999").status_code, 404)

    def test_update_booking_status(self):
        booking = self.make_booking(self.apartment["id"], self.guest["id"])
        response = self.client.put(f"/bookings/{booking['id']}", json={"status": "confirmed"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "confirmed")

    def test_update_booking_invalid_status(self):
        booking = self.make_booking(self.apartment["id"], self.guest["id"])
        response = self.client.put(f"/bookings/{booking['id']}", json={"status": "unknown"})
        self.assertEqual(response.status_code, 400)

    def test_update_booking_dates_recalculates_price(self):
        booking = self.make_booking(self.apartment["id"], self.guest["id"])
        response = self.client.put(f"/bookings/{booking['id']}", json={"check_out": "2026-10-03"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_price"], 4000)  # 2 ночи

    def test_update_booking_cannot_overlap_another(self):
        self.make_booking(self.apartment["id"], self.guest["id"])  # 01.10 - 05.10
        second = self.make_booking(
            self.apartment["id"], self.guest["id"], check_in="2026-10-10", check_out="2026-10-12"
        )
        response = self.client.put(f"/bookings/{second['id']}", json={"check_in": "2026-10-04"})
        self.assertEqual(response.status_code, 409)

    def test_delete_booking(self):
        booking = self.make_booking(self.apartment["id"], self.guest["id"])
        self.assertEqual(self.client.delete(f"/bookings/{booking['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/bookings/{booking['id']}").status_code, 404)
