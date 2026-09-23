from tests.base import ApiTestCase


class OwnerCrudTests(ApiTestCase):
    def test_create_owner(self):
        response = self.client.post(
            "/owners",
            json={"full_name": "Пётр Сидоров", "phone": "+7 911", "email": "petr@example.com"},
        )
        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["full_name"], "Пётр Сидоров")
        self.assertEqual(body["commission_percent"], 20)  # значение по умолчанию

    def test_create_owner_missing_fields(self):
        response = self.client.post("/owners", json={"full_name": "Без телефона"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", response.get_json()["error"])

    def test_create_owner_not_json(self):
        response = self.client.post("/owners", data="просто текст")
        self.assertEqual(response.status_code, 400)

    def test_create_owner_invalid_commission(self):
        for value in (-1, 101, "много"):
            with self.subTest(value=value):
                response = self.client.post(
                    "/owners",
                    json={
                        "full_name": "A",
                        "phone": "1",
                        "email": "a@example.com",
                        "commission_percent": value,
                    },
                )
                self.assertEqual(response.status_code, 400)

    def test_create_owner_duplicate_email(self):
        self.make_owner(email="same@example.com")
        response = self.client.post(
            "/owners", json={"full_name": "B", "phone": "2", "email": "same@example.com"}
        )
        self.assertEqual(response.status_code, 409)

    def test_list_owners(self):
        self.make_owner(email="a@example.com")
        self.make_owner(email="b@example.com")
        response = self.client.get("/owners")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)

    def test_get_owner(self):
        owner = self.make_owner()
        response = self.client.get(f"/owners/{owner['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["email"], "ivan@example.com")

    def test_get_owner_not_found(self):
        self.assertEqual(self.client.get("/owners/999").status_code, 404)

    def test_update_owner(self):
        owner = self.make_owner()
        response = self.client.put(f"/owners/{owner['id']}", json={"phone": "+7 999"})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["phone"], "+7 999")
        self.assertEqual(body["full_name"], "Иван Петров")  # остальное не изменилось

    def test_update_owner_rejects_empty_name(self):
        owner = self.make_owner()
        response = self.client.put(f"/owners/{owner['id']}", json={"full_name": ""})
        self.assertEqual(response.status_code, 400)

    def test_update_owner_not_found(self):
        self.assertEqual(self.client.put("/owners/999", json={"phone": "1"}).status_code, 404)

    def test_delete_owner(self):
        owner = self.make_owner()
        self.assertEqual(self.client.delete(f"/owners/{owner['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/owners/{owner['id']}").status_code, 404)

    def test_delete_owner_with_apartments_is_forbidden(self):
        apartment = self.make_apartment()
        response = self.client.delete(f"/owners/{apartment['owner_id']}")
        self.assertEqual(response.status_code, 409)


class OwnerReportTests(ApiTestCase):
    def test_report_counts_only_confirmed_and_completed(self):
        owner = self.make_owner(commission_percent=25)
        apartment = self.make_apartment(owner_id=owner["id"], price_per_night=1000)
        guest = self.make_client()

        # 4 ночи = 4000, подтверждено -> входит в доход
        confirmed = self.make_booking(apartment["id"], guest["id"])
        self.client.put(f"/bookings/{confirmed['id']}", json={"status": "confirmed"})
        # 2 ночи = 2000, остаётся "new" -> в доход не входит
        self.make_booking(
            apartment["id"], guest["id"], check_in="2026-11-01", check_out="2026-11-03"
        )

        report = self.client.get(f"/owners/{owner['id']}/report").get_json()
        self.assertEqual(report["bookings_count"], 1)
        self.assertEqual(report["income"], 4000)
        self.assertEqual(report["commission"], 1000)  # 25 %
        self.assertEqual(report["payout"], 3000)

    def test_report_for_owner_without_bookings(self):
        owner = self.make_owner()
        report = self.client.get(f"/owners/{owner['id']}/report").get_json()
        self.assertEqual(report["income"], 0)
        self.assertEqual(report["payout"], 0)

    def test_report_owner_not_found(self):
        self.assertEqual(self.client.get("/owners/999/report").status_code, 404)
