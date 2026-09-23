from tests.base import ApiTestCase


class ClientCrudTests(ApiTestCase):
    def test_create_client(self):
        response = self.client.post(
            "/clients",
            json={"full_name": "Олег Орлов", "phone": "+7 921", "email": "oleg@example.com"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["email"], "oleg@example.com")

    def test_create_client_invalid_email(self):
        response = self.client.post(
            "/clients", json={"full_name": "О", "phone": "1", "email": "no-at-sign"}
        )
        self.assertEqual(response.status_code, 400)

    def test_create_client_duplicate_email(self):
        self.make_client(email="dup@example.com")
        response = self.client.post(
            "/clients", json={"full_name": "Дубль", "phone": "1", "email": "dup@example.com"}
        )
        self.assertEqual(response.status_code, 409)

    def test_list_clients(self):
        self.make_client(email="a@example.com")
        self.make_client(email="b@example.com")
        self.assertEqual(len(self.client.get("/clients").get_json()), 2)

    def test_get_client(self):
        guest = self.make_client()
        response = self.client.get(f"/clients/{guest['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["full_name"], "Анна Смирнова")

    def test_get_client_not_found(self):
        self.assertEqual(self.client.get("/clients/999").status_code, 404)

    def test_update_client(self):
        guest = self.make_client()
        response = self.client.put(f"/clients/{guest['id']}", json={"phone": "+7 000"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["phone"], "+7 000")

    def test_update_client_email_conflict(self):
        self.make_client(email="first@example.com")
        second = self.make_client(email="second@example.com")
        response = self.client.put(f"/clients/{second['id']}", json={"email": "first@example.com"})
        self.assertEqual(response.status_code, 409)

    def test_delete_client(self):
        guest = self.make_client()
        self.assertEqual(self.client.delete(f"/clients/{guest['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/clients/{guest['id']}").status_code, 404)

    def test_delete_client_with_bookings_is_forbidden(self):
        apartment = self.make_apartment()
        guest = self.make_client()
        self.make_booking(apartment["id"], guest["id"])
        self.assertEqual(self.client.delete(f"/clients/{guest['id']}").status_code, 409)
