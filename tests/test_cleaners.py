from tests.base import ApiTestCase


class CleanerCrudTests(ApiTestCase):
    def test_create_cleaner_is_active_by_default(self):
        cleaner = self.make_cleaner()
        self.assertIs(cleaner["is_active"], True)

    def test_create_cleaner_missing_phone(self):
        response = self.client.post("/cleaners", json={"full_name": "Без телефона"})
        self.assertEqual(response.status_code, 400)

    def test_create_cleaner_invalid_is_active(self):
        response = self.client.post(
            "/cleaners", json={"full_name": "А", "phone": "1", "is_active": "yes"}
        )
        self.assertEqual(response.status_code, 400)

    def test_list_cleaners(self):
        self.make_cleaner()
        self.make_cleaner(full_name="Елена Кузнецова")
        self.assertEqual(len(self.client.get("/cleaners").get_json()), 2)

    def test_get_cleaner(self):
        cleaner = self.make_cleaner()
        response = self.client.get(f"/cleaners/{cleaner['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["full_name"], "Мария Иванова")

    def test_get_cleaner_not_found(self):
        self.assertEqual(self.client.get("/cleaners/999").status_code, 404)

    def test_update_cleaner_deactivate(self):
        cleaner = self.make_cleaner()
        response = self.client.put(f"/cleaners/{cleaner['id']}", json={"is_active": False})
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.get_json()["is_active"], False)

    def test_delete_cleaner(self):
        cleaner = self.make_cleaner()
        self.assertEqual(self.client.delete(f"/cleaners/{cleaner['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/cleaners/{cleaner['id']}").status_code, 404)
