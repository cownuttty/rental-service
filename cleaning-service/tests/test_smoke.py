import os
import tempfile
import unittest


class CleaningServiceSmokeTests(unittest.TestCase):
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
        self.assertEqual(resp.get_json()["service"], "cleaning-service")

    def test_cleaner_crud(self):
        resp = self.client.post("/cleaners", json={"full_name": "Мария", "phone": "+79991112233"})
        self.assertEqual(resp.status_code, 201)
        cleaner_id = resp.get_json()["id"]
        self.assertEqual(self.client.get(f"/cleaners/{cleaner_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/cleaners/{cleaner_id}").status_code, 204)

    def test_task_creation_from_rental_api(self):
        # Имитируем вызов, который в реальности делает rental-api по HTTP
        resp = self.client.post("/cleaning-tasks", json={
            "apartment_id": 1, "booking_id": 10, "scheduled_date": "2026-10-25"
        })
        self.assertEqual(resp.status_code, 201)
        task = resp.get_json()
        self.assertEqual(task["status"], "planned")

        tasks = self.client.get("/cleaning-tasks").get_json()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["booking_id"], 10)


if __name__ == "__main__":
    unittest.main()
